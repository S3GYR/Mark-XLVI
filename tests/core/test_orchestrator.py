"""Tests for AgentOrchestrator."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from jarvis.core.orchestrator import AgentOrchestrator, Plan
from jarvis.memory.json_store import JsonMemoryStore


def test_parse_plan_json():
    """Plan JSON with steps is parsed correctly."""
    orch = AgentOrchestrator(memory=None, player=MagicMock())
    json_text = """[
        {"id": "1", "description": "Open browser", "tool": "browser_control", "dependencies": []},
        {"id": "2", "description": "Search", "tool": "web_search", "dependencies": ["1"]}
    ]"""
    plan = orch._parse_plan(json_text)
    assert len(plan) == 2
    assert plan[0].id == "1"
    assert plan[1].dependencies == ["1"]


async def test_plan_generation(monkeypatch):
    """Orchestrator can generate a plan using a mocked LLM."""
    from jarvis.llm.client import LLMRouter

    orch = AgentOrchestrator(memory=None, player=MagicMock())
    fake_response = MagicMock()
    fake_response.content = "[{\"id\":\"1\",\"description\":\"test\",\"tool\":\"open_app\",\"dependencies\":[]}]"
    monkeypatch.setattr(
        LLMRouter,
        "chat_with_fallback",
        lambda *args, **kwargs: fake_response,
    )
    plan: Plan = await orch.plan("open chrome")
    assert len(plan.steps) == 1
    assert plan.steps[0].id == "1"


async def test_run_unknown_tool():
    """Unknown tool returns a not-found message."""
    orch = AgentOrchestrator(memory=None, player=MagicMock())
    result = await orch._execute_tool("unknown_tool_xyz", "do something")
    assert "not found" in result.lower()
