"""Tests for LLMClient."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from jarvis.llm.client import LLMClient, ToolDeclaration


def test_normalize_tools():
    """Tool declarations are normalized to LiteLLM format."""
    client = LLMClient()
    decl = ToolDeclaration(
        name="test_tool",
        description="A test tool",
        parameters={"type": "object", "properties": {"x": {"type": "string"}}, "required": ["x"]},
    )
    normalized = client._normalize_tools([decl])
    assert normalized[0]["type"] == "function"
    assert normalized[0]["function"]["name"] == "test_tool"


def test_parse_arguments_dict():
    """Dict tool arguments are returned as-is."""
    client = LLMClient()
    assert client._parse_arguments({"x": 1}) == {"x": 1}


def test_parse_arguments_json_string():
    """JSON string arguments are parsed."""
    client = LLMClient()
    assert client._parse_arguments('{"x": 1}') == {"x": 1}


def test_client_uses_default_model():
    """Default model is taken from settings."""
    client = LLMClient()
    assert client._get_model(None) is not None


@pytest.mark.skip(reason="Requires live LLM API")
def test_chat_real():
    """Smoke test against a real provider."""
    client = LLMClient()
    response = client.chat(messages=[{"role": "user", "content": "Say hello"}])
    assert response.content
