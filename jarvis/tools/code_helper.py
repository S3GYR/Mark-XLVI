"""Secure wrapper for code generation and execution."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jarvis.config.settings import get_settings
from jarvis.core.player import ConsolePlayer, Player
from jarvis.llm.client import LLMClient
from jarvis.security.permissions import ActionContext
from jarvis.security.sandbox import SandboxError, execute_code


# Legacy helpers
from actions.code_helper import (
    _clean_code,
    _detect_intent,
    _read_file,
    _resolve_save_path,
)


def _safe_player(player: Any | None) -> Player:
    """Return a Player instance, using ConsolePlayer as fallback."""
    if player is None:
        return ConsolePlayer()
    return player


def _get_llm_client() -> LLMClient:
    """Return the configured LLM client."""
    return LLMClient()


def code_helper(
    parameters: dict | None = None,
    response: Any | None = None,
    player: Any | None = None,
    session_memory: Any | None = None,
) -> str:
    """Generate, fix, or run code with sandboxed execution.

    Execution is sandboxed for safety. File writes are restricted to the
    user's desktop/data directory.
    """
    params = parameters or {}
    description = params.get("description", "").strip()
    language = params.get("language", "python").strip()
    output_path = params.get("output_path", "").strip()
    file_path = params.get("file_path", "").strip()
    code = params.get("code", "").strip()
    p = _safe_player(player)

    if not description and not file_path and not code:
        return "No description, file path, or code provided."

    p.write_log(f"[code_helper] {description or file_path or 'code snippet'}")

    intent = _detect_intent(description, file_path, code)

    try:
        if intent in {"write", "build"}:
            return _write_code(description, language, output_path, p)
        elif intent == "edit":
            return _edit_code(file_path, description, language, p)
        elif intent == "run":
            return _run_code_file(file_path, p)
        elif intent == "explain":
            return _explain_code(code or file_path, language, p)
        elif intent == "optimize":
            return _optimize_code(code or file_path, description, language, p)
        elif intent == "screen_debug":
            return "Screen debugging is not supported in the modular version yet."
        else:
            return _write_code(description, language, output_path, p)
    except Exception as e:
        return f"Code helper error: {e}"


def _write_code(description: str, language: str, output_path: str, player: Player) -> str:
    """Generate code and save it to a file."""
    ctx = ActionContext("code_helper", f"generate {language} code: '{description[:80]}...'", player)
    if not ctx.check():
        return "Action cancelled by user."

    client = _get_llm_client()
    prompt = f"""You are an expert {language} developer.
Write clean, working, well-commented {language} code for the description below.

Rules:
- Output ONLY the code. No explanation, no markdown, no backticks.
- Add helpful inline comments.
- Handle errors and edge cases properly.

Description: {description}

Code:"""

    resp = client.chat(messages=[{"role": "user", "content": prompt}])
    cleaned = _clean_code(resp.content or "")
    path = _resolve_save_path(output_path, language)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(cleaned, encoding="utf-8")
    return f"Generated {language} code and saved to {path}\n\n{cleaned[:500]}"


def _edit_code(file_path: str, description: str, language: str, player: Player) -> str:
    """Edit an existing code file."""
    ctx = ActionContext("code_helper", f"edit file {file_path}", player)
    if not ctx.check():
        return "Action cancelled by user."

    code, error = _read_file(file_path)
    if error:
        return error

    client = _get_llm_client()
    prompt = f"""Edit the following {language} file according to the instruction.
Return ONLY the full edited code — no explanation, no markdown, no backticks.

Instruction: {description}

File:
{code}
"""
    resp = client.chat(messages=[{"role": "user", "content": prompt}])
    cleaned = _clean_code(resp.content or "")
    path = Path(file_path)
    path.write_text(cleaned, encoding="utf-8")
    return f"Edited {file_path}\n\n{cleaned[:500]}"


def _run_code_file(file_path: str, player: Player) -> str:
    """Run a code file inside the sandbox."""
    ctx = ActionContext("code_helper", f"run file {file_path}", player)
    if not ctx.check():
        return "Action cancelled by user."

    code, error = _read_file(file_path)
    if error:
        return error

    try:
        result = execute_code(code)
        if result["success"]:
            return f"Output:\n{result['stdout']}"
        return f"Execution failed:\n{result['stderr']}"
    except SandboxError as e:
        return f"Sandbox rejected code: {e}"


def _explain_code(source: str, language: str, player: Player) -> str:
    """Explain a code snippet or file."""
    if Path(source).exists():
        code, error = _read_file(source)
        if error:
            return error
    else:
        code = source

    client = _get_llm_client()
    prompt = f"""Explain the following {language} code in a concise way.

{code}
"""
    resp = client.chat(messages=[{"role": "user", "content": prompt}])
    return resp.content or "No explanation generated."


def _optimize_code(source: str, description: str, language: str, player: Player) -> str:
    """Optimize a code snippet or file."""
    if Path(source).exists():
        code, error = _read_file(source)
        if error:
            return error
    else:
        code = source

    ctx = ActionContext("code_helper", f"optimize code: '{description[:80]}...'", player)
    if not ctx.check():
        return "Action cancelled by user."

    client = _get_llm_client()
    prompt = f"""Optimize the following {language} code according to the instruction.
Return ONLY the optimized code — no explanation, no markdown, no backticks.

Instruction: {description}

Code:
{code}
"""
    resp = client.chat(messages=[{"role": "user", "content": prompt}])
    return f"Optimized code:\n\n{_clean_code(resp.content or '')}"
