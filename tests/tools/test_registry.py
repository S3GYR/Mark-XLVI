"""Tests for the tool registry."""

from __future__ import annotations

from jarvis.tools import registry


def test_list_tools():
    """Registry contains the expected tools."""
    tools = registry.list_tools()
    for name in ("open_app", "desktop_control", "computer_control", "send_message", "code_helper", "dev_agent"):
        assert name in tools


def test_get_tool_function():
    """Existing tools return a callable."""
    func = registry.get_tool_function("open_app")
    assert callable(func)


def test_get_tool_declaration():
    """Existing tools return a declaration."""
    decl = registry.get_tool_declaration("open_app")
    assert decl is not None
    assert decl["function"]["name"] == "open_app"


def test_get_tool_declarations():
    """All declarations are returned."""
    decls = registry.get_tool_declarations()
    assert len(decls) >= 6
