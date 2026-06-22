"""Agent orchestrator with planning, memory, and tool execution loops."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from jarvis.config.settings import Settings, get_settings
from jarvis.core.player import ConsolePlayer, Player
from jarvis.llm.client import LLMClient, LLMRouter, ToolCall, ToolDeclaration
from jarvis.memory.store import MemoryStore
from jarvis.observability.logger import get_logger
from jarvis.observability.tracing import instrument_async
from jarvis.tools.registry import get_tool_declarations, get_tool_function

logger = get_logger(__name__)


@dataclass
class Step:
    """A single step in a plan."""

    id: str
    description: str
    tool: str | None = None
    status: str = "pending"  # pending, in_progress, done, failed
    result: str = ""
    dependencies: list[str] = field(default_factory=list)


@dataclass
class Plan:
    """A plan composed of steps."""

    goal: str
    steps: list[Step]
    context: str = ""


class AgentOrchestrator:
    """Hindsight/Agent Zero inspired orchestrator.

    The orchestrator maintains a plan, executes tools step-by-step, and stores
    observations in memory for future sessions.
    """

    def __init__(
        self,
        settings: Settings | None = None,
        llm: LLMClient | None = None,
        memory: MemoryStore | None = None,
        player: Player | None = None,
    ):
        self.settings = settings or get_settings()
        self.llm = llm or LLMClient()
        self.router = LLMRouter(self.llm)
        self.memory = memory
        self.player = player or ConsolePlayer()
        self._tools = [
            ToolDeclaration(
                name=decl["function"]["name"],
                description=decl["function"]["description"],
                parameters=decl["function"]["parameters"],
            )
            for decl in get_tool_declarations()
        ]

    @instrument_async("orchestrator.plan")
    async def plan(self, goal: str) -> Plan:
        """Generate a plan for the given goal."""
        memories = ""
        if self.memory:
            memories = await self.memory.format_for_prompt(self.settings.memory_max_chars)

        prompt = (
            "You are a planning assistant. Break the following goal into small, "
            "executable steps. Each step should optionally use one of the available tools.\n\n"
            f"Goal: {goal}\n\n"
            f"Available tools:\n{self._format_tools()}\n\n"
            f"User context:\n{memories}\n\n"
            "Return a JSON list of steps with keys: id, description, tool, dependencies."
        )

        response = self.router.chat_with_fallback(
            messages=[{"role": "user", "content": prompt}],
        )
        steps = self._parse_plan(response.content or "[]")
        return Plan(goal=goal, steps=steps, context=memories)

    @instrument_async("orchestrator.execute_plan")
    async def execute_plan(self, plan: Plan) -> str:
        """Execute a plan and return the final summary."""
        completed: dict[str, str] = {}

        for step in plan.steps:
            step.status = "in_progress"
            self.player.write_log(f"[plan] {step.id}: {step.description}")
            logger.info("plan_step_started", step_id=step.id, description=step.description)

            try:
                if step.tool:
                    result = await self._execute_tool(step.tool, step.description)
                else:
                    result = await self._execute_direct(step.description)
                step.status = "done"
                step.result = result
                completed[step.id] = result
            except Exception as e:
                step.status = "failed"
                step.result = str(e)
                logger.error("plan_step_failed", step_id=step.id, error=str(e))
                self.player.write_log(f"[plan] {step.id} failed: {e}")

        return self._summarize_plan(plan)

    @instrument_async("orchestrator.run")
    async def run(self, goal: str) -> str:
        """Plan and execute a goal in one call."""
        plan = await self.plan(goal)
        return await self.execute_plan(plan)

    @instrument_async("orchestrator.execute_tool")
    async def _execute_tool(self, tool_name: str, description: str) -> str:
        """Execute a single tool by name."""
        func = get_tool_function(tool_name)
        if func is None:
            return f"Tool '{tool_name}' not found"

        # Use the LLM to extract parameters from the description
        params = await self._extract_parameters(tool_name, description)
        self.player.write_log(f"[tool] {tool_name}({params})")

        if asyncio.iscoroutinefunction(func):
            result = await func(params, player=self.player)
        else:
            result = func(params, player=self.player)
        return str(result)

    async def _execute_direct(self, description: str) -> str:
        """Execute a step that does not require a tool."""
        response = self.router.chat_with_fallback(
            messages=[{"role": "user", "content": description}],
        )
        return response.content or ""

    async def _extract_parameters(self, tool_name: str, description: str) -> dict[str, Any]:
        """Ask the LLM to extract parameters for a tool call."""
        decl = next((t for t in self._tools if t.name == tool_name), None)
        if decl is None:
            return {}

        prompt = (
            f"Extract parameters for the tool '{tool_name}' from the description.\n"
            f"Tool schema: {decl.parameters}\n"
            f"Description: {description}\n\n"
            "Return ONLY a JSON object with the parameters."
        )
        response = self.router.chat_with_fallback(
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.content or "{}"
        import json

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {}

    def _format_tools(self) -> str:
        """Format tool descriptions for the planner prompt."""
        lines = []
        for tool in self._tools:
            lines.append(f"- {tool.name}: {tool.description}")
        return "\n".join(lines)

    @staticmethod
    def _parse_plan(content: str) -> list[Step]:
        """Parse a plan returned by the LLM."""
        import json
        import re

        # Try to extract JSON from markdown
        if "```" in content:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content)
            if match:
                content = match.group(1)

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return []

        if not isinstance(data, list):
            return []

        steps = []
        for item in data:
            steps.append(
                Step(
                    id=item.get("id", str(len(steps) + 1)),
                    description=item.get("description", ""),
                    tool=item.get("tool") or None,
                    dependencies=item.get("dependencies", []),
                )
            )
        return steps

    def _summarize_plan(self, plan: Plan) -> str:
        """Create a human-readable summary of plan execution."""
        lines = [f"Plan: {plan.goal}", ""]
        for step in plan.steps:
            icon = "✅" if step.status == "done" else "❌"
            lines.append(f"{icon} {step.id}: {step.description}")
            if step.result:
                lines.append(f"   → {step.result[:200]}")
        return "\n".join(lines)

    async def remember(self, category: str, key: str, value: str) -> None:
        """Persist an observation to memory."""
        if self.memory:
            await self.memory.save(category, key, value)
            logger.info("memory_saved", category=category, key=key)
