"""Tests for the secure sandbox."""

from __future__ import annotations

import pytest

from jarvis.security.sandbox import (
    CodeSafetyError,
    SandboxError,
    execute_code,
    validate_code,
)


def test_validate_safe_code():
    """Accept safe mathematical code."""
    validate_code("x = 1 + 2\nprint(x)")


def test_validate_rejects_exec():
    """Reject code containing exec()."""
    with pytest.raises(CodeSafetyError):
        validate_code("exec('print(1)')")


def test_validate_rejects_subprocess():
    """Reject code importing subprocess."""
    with pytest.raises(CodeSafetyError):
        validate_code("import subprocess\nsubprocess.run(['ls'])")


def test_validate_rejects_eval():
    """Reject code containing eval()."""
    with pytest.raises(CodeSafetyError):
        validate_code("eval('1+1')")


def test_execute_safe_code():
    """Execute a simple calculation in the sandbox."""
    result = execute_code("x = 1 + 2\nprint(x)")
    assert result["success"]
    assert result["stdout"] == "3"


def test_execute_code_with_main():
    """Execute code that defines a main function."""
    code = """
def main():
    return 42
"""
    result = execute_code(code)
    assert result["stdout"] == "42"


def test_execute_rejects_unsafe_code():
    """Sandbox refuses to run forbidden code."""
    with pytest.raises(CodeSafetyError):
        execute_code("import os\nos.system('ls')")
