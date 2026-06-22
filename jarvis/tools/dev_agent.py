"""Secure wrapper for the development agent."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from jarvis.config.paths import DATA_DIR
from jarvis.core.player import ConsolePlayer, Player
from jarvis.llm.client import LLMClient
from jarvis.security.permissions import ActionContext


# Legacy helpers
from actions.dev_agent import (
    _classify_error,
    _has_error,
    _parse_traceback,
    _plan_project,
    _strip_fences,
    _write_file,
)


def _safe_player(player: Any | None) -> Player:
    """Return a Player instance, using ConsolePlayer as fallback."""
    if player is None:
        return ConsolePlayer()
    return player


# Default projects directory moved outside source tree
PROJECTS_DIR = DATA_DIR / "projects"
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)


def dev_agent(
    parameters: dict | None = None,
    response: Any | None = None,
    player: Any | None = None,
    session_memory: Any | None = None,
) -> str:
    """Create or fix a multi-file project with user confirmation.

    Generated projects are stored in the user data directory. Running code is
    sandboxed: pip installs are allowed only after explicit confirmation.
    """
    params = parameters or {}
    description = params.get("description", "").strip()
    language = params.get("language", "python").strip()
    fix_mode = params.get("fix_mode", False)
    p = _safe_player(player)

    if not description:
        return "No project description provided."

    ctx = ActionContext("dev_agent", f"create project: '{description[:80]}...'", p)
    if not ctx.check():
        return "Action cancelled by user."

    p.write_log(f"[dev_agent] {description[:80]}...")

    try:
        if fix_mode:
            return _fix_project(params, p)
        return _create_project(description, language, p)
    except Exception as e:
        return f"Dev agent error: {e}"


def _create_project(description: str, language: str, player: Player) -> str:
    """Create a new project from description."""
    plan = _plan_project(description, language)
    project_name = plan.get("project_name", "project")
    project_dir = PROJECTS_DIR / project_name
    project_dir.mkdir(parents=True, exist_ok=True)

    files = plan.get("files", [])
    already_written: dict[str, str] = {}

    for file_info in files:
        try:
            result = _write_file(
                file_info,
                description,
                files,
                language,
                project_dir,
                already_written,
            )
            player.write_log(f"[dev_agent] wrote {file_info['path']}")
        except Exception as e:
            return f"Failed to write {file_info.get('path', '?')}: {e}"

    # Optionally install dependencies
    dependencies = plan.get("dependencies", [])
    if dependencies:
        dep_ctx = ActionContext(
            "dev_agent",
            f"install dependencies: {', '.join(dependencies)}",
            player,
        )
        if dep_ctx.check():
            _install_dependencies(project_dir, dependencies)

    run_command = plan.get("run_command", "")
    return (
        f"Project '{project_name}' created at {project_dir}\n"
        f"Files: {len(files)}\n"
        f"Run command: {run_command or 'none'}"
    )


def _fix_project(params: dict, player: Player) -> str:
    """Fix an existing project based on error output."""
    project_dir = Path(params.get("project_dir", PROJECTS_DIR))
    error_output = params.get("error_output", "")
    language = params.get("language", "python")

    if not project_dir.exists():
        return f"Project directory not found: {project_dir}"
    if not error_output:
        return "No error output provided."

    ctx = ActionContext("dev_agent", f"fix project at {project_dir}", player)
    if not ctx.check():
        return "Action cancelled by user."

    files = [str(p) for p in project_dir.rglob("*") if p.is_file() and p.suffix == ".py"]
    file_path, line_no = _parse_traceback(error_output, files)
    error_type = _classify_error(error_output)

    if not file_path:
        return "Could not identify the failing file from the traceback."

    try:
        content = Path(file_path).read_text(encoding="utf-8")
    except Exception as e:
        return f"Could not read {file_path}: {e}"

    client = LLMClient()
    prompt = f"""Fix the following {language} file that fails with this error.
Return ONLY the corrected code — no explanation, no markdown, no backticks.

Error ({error_type}):
{error_output[:2000]}

File:
{content}

Corrected code:"""

    resp = client.chat(messages=[{"role": "user", "content": prompt}])
    fixed = _strip_fences(resp.content or "")
    Path(file_path).write_text(fixed, encoding="utf-8")
    return f"Fixed {file_path} (line {line_no})\n\n{fixed[:500]}"


def _install_dependencies(project_dir: Path, dependencies: list[str]) -> str:
    """Install dependencies in a subprocess with timeout."""
    try:
        result = subprocess.run(
            [subprocess.sys.executable, "-m", "pip", "install", *dependencies],
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            return f"Installed: {', '.join(dependencies)}"
        return f"Install failed: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Dependency install timed out."
    except Exception as e:
        return f"Install error: {e}"
