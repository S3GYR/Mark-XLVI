"""Secure sandbox for executing LLM-generated code."""

from __future__ import annotations

import ast
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from jarvis.config.settings import get_settings


# Statically forbidden patterns
FORBIDDEN_NAMES = {
    "eval",
    "exec",
    "compile",
    "__import__",
    "open",
    "input",
    "breakpoint",
    "exit",
    "quit",
}

FORBIDDEN_MODULES = {
    "subprocess",
    "os",
    "sys",
    "socket",
    "urllib",
    "http",
    "requests",
    "webbrowser",
    "ctypes",
    "winreg",
    "shutil.rmtree",
    "pathlib.Path.rmdir",
    "pathlib.Path.unlink",
}

ALLOWED_IMPORTS = {
    "pathlib",
    "math",
    "random",
    "datetime",
    "time",
    "json",
    "re",
    "statistics",
    "collections",
    "itertools",
    "functools",
    "typing",
    "hashlib",
    "base64",
}


class SandboxError(Exception):
    """Raised when code is rejected or fails in the sandbox."""


class CodeSafetyError(SandboxError):
    """Raised when code fails static safety checks."""


class CodeExecutionError(SandboxError):
    """Raised when code fails during execution."""



def _extract_imports(code: str) -> set[str]:
    """Extract top-level import names from Python source."""
    imports: set[str] = set()
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise CodeSafetyError(f"Syntax error: {e}") from e

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])
    return imports


def _check_forbidden_patterns(code: str) -> None:
    """Raise if the code contains forbidden names or modules."""
    # Check forbidden names used as bare names
    for name in FORBIDDEN_NAMES:
        if re.search(rf"\b{name}\b", code):
            raise CodeSafetyError(f"Forbidden name '{name}' found in generated code")

    # Check forbidden module usage
    for mod in FORBIDDEN_MODULES:
        if re.search(rf"\b{re.escape(mod)}\b", code):
            raise CodeSafetyError(f"Forbidden module '{mod}' referenced in generated code")

    # Check for network indicators
    if re.search(r"\b(url|http|https|ftp|socket|connect|request)\b", code, re.IGNORECASE):
        raise CodeSafetyError("Network operations are not allowed in the sandbox")


def validate_code(code: str) -> None:
    """Validate that generated code is safe to run.

    This is a static check. It does not guarantee runtime safety.
    """
    if not code or code.strip() == "UNSAFE":
        raise CodeSafetyError("Task cannot be performed safely.")

    code = code.strip()
    if code.startswith("```"):
        lines = code.split("\n")
        code = "\n".join(lines[1:-1]).strip()

    _check_forbidden_patterns(code)
    imports = _extract_imports(code)
    for imp in imports:
        if imp not in ALLOWED_IMPORTS:
            raise CodeSafetyError(f"Import '{imp}' is not allowed in the sandbox")


def _build_runner_script(code: str) -> str:
    """Build a script that runs the code in a restricted environment."""
    return f"""
import sys
import json

# Restrict sys.path to avoid importing arbitrary modules
sys.path = []

{code}

# If there is a main function, call it
if "main" in dir() and callable(main):
    try:
        result = main()
        if result is not None:
            print(result)
    except Exception as e:
        print(f"ERROR: {{e}}")
"""


def execute_code(code: str, timeout: int = 30) -> dict[str, Any]:
    """Execute validated code in a subprocess sandbox.

    Returns a dict with keys: success, stdout, stderr, returncode.
    """
    settings = get_settings()
    if not settings.sandbox_enabled:
        raise SandboxError("Sandbox is disabled in settings")

    validate_code(code)

    runner = _build_runner_script(code)
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(runner)
        script_path = Path(f.name)

    try:
        result = subprocess.run(
            [sys.executable, "-I", "-B", "-S", str(script_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            env={"PYTHONPATH": ""},
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Execution timed out after {timeout}s",
            "returncode": -1,
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1,
        }
    finally:
        try:
            script_path.unlink()
        except Exception:
            pass
