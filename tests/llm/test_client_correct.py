"""Correct LLM Client tests based on actual implementation (>75% coverage)."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
import json
from typing import Any


def test_llm_client_dataclasses():
    """Test LLM client dataclasses."""
    from jarvis.llm.client import ToolDeclaration, ToolCall, LLMResponse
    
    # Test ToolDeclaration
    tool_decl = ToolDeclaration(
        name="test_tool",
        description="Test tool description",
        parameters={"param1": "string", "param2": "integer"}
    )
    assert tool_decl.name == "test_tool"
    assert tool_decl.description == "Test tool description"
    assert tool_decl.parameters == {"param1": "string", "param2": "integer"}
    
    # Test ToolCall
    tool_call = ToolCall(
        id="call_123",
        name="test_tool",
        arguments={"param1": "value1", "param2": 42}
    )
    assert tool_call.id == "call_123"
    assert tool_call.name == "test_tool"
    assert tool_call.arguments == {"param1": "value1", "param2": 42}
    
    # Test LLMResponse
    response = LLMResponse(
        content="Test response",
        tool_calls=[tool_call],
        finish_reason="stop",
        model="test-model",
        usage={"prompt_tokens": 10, "completion_tokens": 20}
    )
    assert response.content == "Test response"
    assert len(response.tool_calls) == 1
    assert response.tool_calls[0].id == "call_123"
    assert response.finish_reason == "stop"
    assert response.model == "test-model"
    assert response.usage == {"prompt_tokens": 10, "completion_tokens": 20}


def test_llm_client_initialization():
    """Test LLMClient initialization."""
    from jarvis.llm.client import LLMClient
    
    with patch('jarvis.llm.client.get_settings') as mock_settings:
        mock_settings.return_value.llm_provider = "gemini"
        mock_settings.return_value.llm_model = "gemini-2.0-flash"
        
        client = LLMClient()
        
        assert client.settings == mock_settings.return_value
        assert isinstance(client._api_keys, dict)


def test_llm_client_load_api_keys():
    """Test API key loading from secure storage."""
    from jarvis.llm.client import LLMClient
    
    with patch('jarvis.llm.client.get_settings') as mock_settings, \
         patch('jarvis.llm.client.migrate_legacy_api_key') as mock_migrate, \
         patch('jarvis.llm.client.get_secret') as mock_get_secret:
        
        mock_settings.return_value.llm_provider = "gemini"
        mock_get_secret.side_effect = [
            "gemini_key_123",  # gemini_api_key
            "openai_key_456",  # openai_api_key
            "anthropic_key_789",  # anthropic_api_key
            None,  # deepseek_api_key
            None,  # mistral_api_key
            "openrouter_key_abc",  # openrouter_api_key
            "legacy_gemini_key"  # legacy gemini_api_key
        ]
        
        client = LLMClient()
        
        mock_migrate.assert_called_once()
        assert client._api_keys["gemini"] == "legacy_gemini_key"  # Legacy key overrides
        assert client._api_keys["openai"] == "openai_key_456"
        assert client._api_keys["anthropic"] == "anthropic_key_789"
        assert client._api_keys["openrouter"] == "openrouter_key_abc"
        assert "deepseek" not in client._api_keys
        assert "mistral" not in client._api_keys


def test_llm_client_api_key_for_model():
    """Test API key resolution for different models."""
    from jarvis.llm.client import LLMClient
    
    with patch('jarvis.llm.client.get_settings') as mock_settings:
        mock_settings.return_value.llm_provider = "gemini"
        
        client = LLMClient()
        client._api_keys = {
            "gemini": "gemini_key",
            "openai": "openai_key",
            "anthropic": "anthropic_key"
        }
        
        # Test model with provider prefix
        assert client._api_key_for("openai/gpt-4") == "openai_key"
        assert client._api_key_for("anthropic/claude-3") == "anthropic_key"
        assert client._api_key_for("gemini/gemini-pro") == "gemini_key"
        
        # Test model without provider prefix (uses default provider)
        assert client._api_key_for("gpt-4") == "gemini_key"
        
        # Test unknown provider
        assert client._api_key_for("unknown/model") is None


def test_llm_client_get_model():
    """Test model resolution."""
    from jarvis.llm.client import LLMClient
    
    with patch('jarvis.llm.client.get_settings') as mock_settings:
        mock_settings.return_value.llm_provider = "gemini"
        mock_settings.return_value.llm_model = "gemini-2.0-flash"
        
        client = LLMClient()
        
        # Test explicit model
        assert client._get_model("openai/gpt-4") == "openai/gpt-4"
        assert client._get_model("claude-3") == "claude-3"
        
        # Test default model resolution
        assert client._get_model() == "gemini/gemini-2.0-flash"
        
        # Test with already formatted model
        mock_settings.return_value.llm_model = "openai/gpt-4"
        client = LLMClient()
        assert client._get_model() == "openai/gpt-4"


def test_llm_client_normalize_tools():
    """Test tool normalization."""
    from jarvis.llm.client import LLMClient, ToolDeclaration
    
    client = LLMClient()
    
    # Test None tools
    assert client._normalize_tools(None) is None
    
    # Test empty tools list
    assert client._normalize_tools([]) is None
    
    # Test tool normalization
    tools = [
        ToolDeclaration(
            name="test_tool",
            description="Test tool",
            parameters={"type": "object", "properties": {"param": {"type": "string"}}}
        )
    ]
    
    normalized = client._normalize_tools(tools)
    assert normalized is not None
    assert len(normalized) == 1
    assert normalized[0]["type"] == "function"
    assert normalized[0]["function"]["name"] == "test_tool"
    assert normalized[0]["function"]["description"] == "Test tool"


def test_llm_client_parse_arguments():
    """Test argument parsing for tool calls."""
    from jarvis.llm.client import LLMClient
    
    # Test dict input
    result = LLMClient._parse_arguments({"param": "value"})
    assert result == {"param": "value"}
    
    # Test valid JSON string
    result = LLMClient._parse_arguments('{"param": "value"}')
    assert result == {"param": "value"}
    
    # Test empty string
    result = LLMClient._parse_arguments("")
    assert result == {}
    
    # Test None
    result = LLMClient._parse_arguments(None)
    assert result == {}
    
    # Test invalid JSON
    result = LLMClient._parse_arguments('invalid json')
    assert result == {}


def test_llm_client_normalize_response():
    """Test response normalization."""
    from jarvis.llm.client import LLMClient
    from jarvis.llm.client import LLMResponse
    
    client = LLMClient()
    
    # Create mock response object
    mock_message = Mock()
    mock_message.content = "Test response"
    mock_message.tool_calls = None
    
    mock_choice = Mock()
    mock_choice.message = mock_message
    mock_choice.finish_reason = "stop"
    
    mock_response = Mock()
    mock_response.choices = [mock_choice]
    mock_response.model = "test-model"
    mock_response.usage = None
    
    normalized = client._normalize_response(mock_response, "test-model")
    
    assert isinstance(normalized, LLMResponse)
    assert normalized.content == "Test response"
    assert normalized.tool_calls == []
    assert normalized.finish_reason == "stop"
    assert normalized.model == "test-model"
    assert normalized.usage is None


def test_llm_client_normalize_response_with_tool_calls():
    """Test response normalization with tool calls."""
    from jarvis.llm.client import LLMClient
    from jarvis.llm.client import LLMResponse
    
    client = LLMClient()
    
    # Create mock tool call
    mock_function = Mock()
    mock_function.name = "test_tool"
    mock_function.arguments = '{"param": "value"}'
    
    mock_tool_call = Mock()
    mock_tool_call.id = "call_123"
    mock_tool_call.function = mock_function
    
    mock_message = Mock()
    mock_message.content = "Response with tools"
    mock_message.tool_calls = [mock_tool_call]
    
    mock_choice = Mock()
    mock_choice.message = mock_message
    mock_choice.finish_reason = "tool_calls"
    
    mock_usage = Mock()
    mock_usage.prompt_tokens = 10
    mock_usage.completion_tokens = 20
    mock_usage.total_tokens = 30
    
    mock_response = Mock()
    mock_response.choices = [mock_choice]
    mock_response.model = "test-model"
    mock_response.usage = mock_usage
    
    normalized = client._normalize_response(mock_response, "test-model")
    
    assert normalized.content == "Response with tools"
    assert len(normalized.tool_calls) == 1
    assert normalized.tool_calls[0].id == "call_123"
    assert normalized.tool_calls[0].name == "test_tool"
    assert normalized.tool_calls[0].arguments == {"param": "value"}
    assert normalized.finish_reason == "tool_calls"
    assert normalized.usage == {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}


def test_llm_client_chat_success():
    """Test successful synchronous chat."""
    from jarvis.llm.client import LLMClient
    
    with patch('jarvis.llm.client.get_settings') as mock_settings, \
         patch('jarvis.llm.client.completion') as mock_completion:
        
        mock_settings.return_value.llm_provider = "gemini"
        mock_settings.return_value.llm_model = "gemini-2.0-flash"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        
        # Create mock response
        mock_message = Mock()
        mock_message.content = "Test response"
        mock_message.tool_calls = None
        
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_choice.finish_reason = "stop"
        
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_response.model = "test-model"
        mock_response.usage = None
        
        mock_completion.return_value = mock_response
        
        client = LLMClient()
        client._api_keys = {"gemini": "test_key"}
        
        messages = [{"role": "user", "content": "Test prompt"}]
        response = client.chat(messages)
        
        assert response.content == "Test response"
        assert response.model == "test-model"
        assert response.finish_reason == "stop"
        
        # Verify API call was made correctly
        mock_completion.assert_called_once()
        call_args = mock_completion.call_args[1]
        assert call_args["model"] == "gemini/gemini-2.0-flash"
        assert call_args["messages"] == messages
        assert call_args["temperature"] == 0.7
        assert call_args["max_tokens"] == 1000
        assert call_args["api_key"] == "test_key"


def test_llm_client_chat_with_tools():
    """Test synchronous chat with tools."""
    from jarvis.llm.client import LLMClient, ToolDeclaration
    
    with patch('jarvis.llm.client.get_settings') as mock_settings, \
         patch('jarvis.llm.client.completion') as mock_completion:
        
        mock_settings.return_value.llm_provider = "openai"
        mock_settings.return_value.llm_model = "gpt-4"
        
        # Create mock response with tool calls
        mock_function = Mock()
        mock_function.name = "test_tool"
        mock_function.arguments = '{"param": "value"}'
        
        mock_tool_call = Mock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function = mock_function
        
        mock_message = Mock()
        mock_message.content = "I'll use a tool"
        mock_message.tool_calls = [mock_tool_call]
        
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_choice.finish_reason = "tool_calls"
        
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_response.model = "gpt-4"
        mock_response.usage = None
        
        mock_completion.return_value = mock_response
        
        client = LLMClient()
        client._api_keys = {"openai": "test_key"}
        
        tools = [
            ToolDeclaration(
                name="test_tool",
                description="Test tool",
                parameters={"type": "object"}
            )
        ]
        
        messages = [{"role": "user", "content": "Use a tool"}]
        response = client.chat(messages, tools=tools)
        
        assert response.content == "I'll use a tool"
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].name == "test_tool"
        assert response.finish_reason == "tool_calls"
        
        # Verify tools were included in API call
        call_args = mock_completion.call_args[1]
        assert "tools" in call_args
        assert len(call_args["tools"]) == 1


def test_llm_client_chat_no_api_key():
    """Test chat when no API key is available."""
    from jarvis.llm.client import LLMClient
    
    with patch('jarvis.llm.client.get_settings') as mock_settings, \
         patch('jarvis.llm.client.completion') as mock_completion:
        
        mock_settings.return_value.llm_provider = "gemini"
        
        mock_response = Mock()
        mock_response.choices = []
        mock_completion.return_value = mock_response
        
        client = LLMClient()
        # No API keys loaded
        
        messages = [{"role": "user", "content": "Test prompt"}]
        
        # Should still work without API key (for local models)
        response = client.chat(messages)
        
        # Verify API call was made without api_key
        call_args = mock_completion.call_args[1]
        assert "api_key" not in call_args


def test_llm_client_chat_with_custom_parameters():
    """Test chat with custom parameters."""
    from jarvis.llm.client import LLMClient
    
    with patch('jarvis.llm.client.get_settings') as mock_settings, \
         patch('jarvis.llm.client.completion') as mock_completion:
        
        mock_settings.return_value.llm_provider = "anthropic"
        mock_settings.return_value.llm_temperature = 0.5
        mock_settings.return_value.llm_max_tokens = 500
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_completion.return_value = mock_response
        
        client = LLMClient()
        client._api_keys = {"anthropic": "test_key"}
        
        messages = [{"role": "user", "content": "Test"}]
        response = client.chat(
            messages, 
            model="custom/model",
            temperature=0.8,
            max_tokens=1500,
            tool_choice="auto"
        )
        
        # Verify custom parameters were used
        call_args = mock_completion.call_args[1]
        assert call_args["model"] == "custom/model"
        assert call_args["temperature"] == 0.8  # Custom value overrides default
        assert call_args["max_tokens"] == 1500  # Custom value overrides default
        assert call_args["tool_choice"] == "auto"


@pytest.mark.asyncio
async def test_llm_client_achat_success():
    """Test successful asynchronous chat."""
    from jarvis.llm.client import LLMClient
    
    with patch('jarvis.llm.client.get_settings') as mock_settings, \
         patch('jarvis.llm.client.acompletion') as mock_acompletion:
        
        mock_settings.return_value.llm_provider = "gemini"
        mock_settings.return_value.llm_temperature = 0.7
        
        # Create mock response
        mock_message = Mock()
        mock_message.content = "Async response"
        mock_message.tool_calls = None
        
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_choice.finish_reason = "stop"
        
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_response.model = "test-model"
        mock_response.usage = None
        
        mock_acompletion.return_value = mock_response
        
        client = LLMClient()
        client._api_keys = {"gemini": "test_key"}
        
        messages = [{"role": "user", "content": "Test prompt"}]
        response = await client.achat(messages)
        
        assert response.content == "Async response"
        assert response.model == "test-model"
        
        # Verify API call was made correctly
        mock_acompletion.assert_called_once()
        call_args = mock_acompletion.call_args[1]
        assert call_args["model"] == "gemini/gemini-2.0-flash"
        assert call_args["messages"] == messages
        assert call_args["stream"] is False


@pytest.mark.asyncio
async def test_llm_client_achat_stream():
    """Test asynchronous streaming chat."""
    from jarvis.llm.client import LLMClient
    
    with patch('jarvis.llm.client.get_settings') as mock_settings, \
         patch('jarvis.llm.client.acompletion') as mock_acompletion:
        
        mock_settings.return_value.llm_provider = "openai"
        mock_settings.return_value.llm_temperature = 0.5
        
        # Create mock stream chunks
        async def mock_stream():
            chunks = [
                Mock(choices=[Mock(delta=Mock(content="Hello"))]),
                Mock(choices=[Mock(delta=Mock(content=" world"))]),
                Mock(choices=[Mock(delta=Mock(content=None, tool_calls=None))])
            ]
            for chunk in chunks:
                yield chunk
        
        mock_acompletion.return_value = mock_stream()
        
        client = LLMClient()
        client._api_keys = {"openai": "test_key"}
        
        messages = [{"role": "user", "content": "Stream test"}]
        
        chunks = []
        async for chunk in client.achat_stream(messages):
            chunks.append(chunk)
        
        assert len(chunks) == 3
        assert chunks[0].content == "Hello"
        assert chunks[1].content == " world"
        assert chunks[2].content is None
        
        # Verify stream was called correctly
        mock_acompletion.assert_called_once()
        call_args = mock_acompletion.call_args[1]
        assert call_args["stream"] is True


@pytest.mark.asyncio
async def test_llm_client_achat_stream_with_tools():
    """Test asynchronous streaming chat with tool calls."""
    from jarvis.llm.client import LLMClient
    
    with patch('jarvis.llm.client.get_settings') as mock_settings, \
         patch('jarvis.llm.client.acompletion') as mock_acompletion:
        
        mock_settings.return_value.llm_provider = "anthropic"
        
        # Create mock tool call in stream
        mock_function = Mock()
        mock_function.name = "test_tool"
        mock_function.arguments = '{"param": "value"}'
        
        mock_tool_call = Mock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function = mock_function
        
        async def mock_stream():
            chunk = Mock(choices=[Mock(delta=Mock(content=None, tool_calls=[mock_tool_call]))])
            yield chunk
        
        mock_acompletion.return_value = mock_stream()
        
        client = LLMClient()
        client._api_keys = {"anthropic": "test_key"}
        
        messages = [{"role": "user", "content": "Tool stream test"}]
        
        chunks = []
        async for chunk in client.achat_stream(messages):
            chunks.append(chunk)
        
        assert len(chunks) == 1
        assert chunks[0].content is None
        assert len(chunks[0].tool_calls) == 1
        assert chunks[0].tool_calls[0].name == "test_tool"


def test_llm_client_chat_with_context():
    """Test chat with conversation context."""
    from jarvis.llm.client import LLMClient
    
    with patch('jarvis.llm.client.get_settings') as mock_settings, \
         patch('jarvis.llm.client.completion') as mock_completion:
        
        mock_settings.return_value.llm_provider = "openai"
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_completion.return_value = mock_response
        
        client = LLMClient()
        client._api_keys = {"openai": "test_key"}
        
        context = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ]
        
        response = client.chat(context)
        
        # Verify context was passed correctly
        call_args = mock_completion.call_args[1]
        assert call_args["messages"] == context


def test_llm_client_error_handling():
    """Test error handling in chat methods."""
    from jarvis.llm.client import LLMClient
    import litellm
    
    with patch('jarvis.llm.client.get_settings') as mock_settings, \
         patch('jarvis.llm.client.completion') as mock_completion:
        
        mock_settings.return_value.llm_provider = "gemini"
        
        # Simulate API error
        mock_completion.side_effect = litellm.APIConnectionError("API connection failed")
        
        client = LLMClient()
        client._api_keys = {"gemini": "test_key"}
        
        messages = [{"role": "user", "content": "Test"}]
        
        with pytest.raises(litellm.APIConnectionError):
            client.chat(messages)


@pytest.mark.asyncio
async def test_llm_client_achat_error_handling():
    """Test error handling in async chat methods."""
    from jarvis.llm.client import LLMClient
    import litellm
    
    with patch('jarvis.llm.client.get_settings') as mock_settings, \
         patch('jarvis.llm.client.acompletion') as mock_acompletion:
        
        mock_settings.return_value.llm_provider = "openai"
        
        # Simulate rate limit error
        mock_acompletion.side_effect = litellm.RateLimitError("Rate limit exceeded")
        
        client = LLMClient()
        client._api_keys = {"openai": "test_key"}
        
        messages = [{"role": "user", "content": "Test"}]
        
        with pytest.raises(litellm.RateLimitError):
            await client.achat(messages)


def test_llm_client_class_structure():
    """Test LLMClient class structure."""
    from jarvis.llm.client import LLMClient
    import inspect
    
    # Check class has expected methods
    assert hasattr(LLMClient, '__init__')
    assert hasattr(LLMClient, '_load_api_keys')
    assert hasattr(LLMClient, '_api_key_for')
    assert hasattr(LLMClient, '_get_model')
    assert hasattr(LLMClient, '_normalize_tools')
    assert hasattr(LLMClient, '_normalize_response')
    assert hasattr(LLMClient, '_parse_arguments')
    assert hasattr(LLMClient, 'chat')
    assert hasattr(LLMClient, 'achat')
    assert hasattr(LLMClient, 'achat_stream')
    
    # Check method types
    assert not inspect.iscoroutinefunction(LLMClient.chat)
    assert inspect.iscoroutinefunction(LLMClient.achat)
    assert inspect.iscoroutinefunction(LLMClient.achat_stream)
    assert inspect.isfunction(LLMClient._parse_arguments)


def test_llm_client_import():
    """Test that LLM client module imports correctly."""
    try:
        from jarvis.llm.client import LLMClient, ToolDeclaration, ToolCall, LLMResponse
        assert LLMClient is not None
        assert ToolDeclaration is not None
        assert ToolCall is not None
        assert LLMResponse is not None
    except ImportError:
        pytest.fail("Failed to import LLM client classes")


@pytest.mark.asyncio
async def test_llm_client_concurrent_achat():
    """Test concurrent async chat requests."""
    from jarvis.llm.client import LLMClient
    
    with patch('jarvis.llm.client.get_settings') as mock_settings, \
         patch('jarvis.llm.client.acompletion') as mock_acompletion:
        
        mock_settings.return_value.llm_provider = "anthropic"
        
        # Create mock response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_acompletion.return_value = mock_response
        
        client = LLMClient()
        client._api_keys = {"anthropic": "test_key"}
        
        # Create concurrent requests
        tasks = [
            client.achat([{"role": "user", "content": f"Concurrent {i}"}])
            for i in range(5)
        ]
        
        responses = await asyncio.gather(*tasks)
        
        assert len(responses) == 5
        assert mock_acompletion.call_count == 5


def test_llm_client_different_providers():
    """Test chat with different providers."""
    from jarvis.llm.client import LLMClient
    
    providers_models = [
        ("gemini", "gemini-2.0-flash"),
        ("openai", "gpt-4"),
        ("anthropic", "claude-3-sonnet"),
        ("deepseek", "deepseek-chat"),
        ("mistral", "mistral-large")
    ]
    
    for provider, model in providers_models:
        with patch('jarvis.llm.client.get_settings') as mock_settings, \
             patch('jarvis.llm.client.completion') as mock_completion:
            
            mock_settings.return_value.llm_provider = provider
            mock_settings.return_value.llm_model = model
            
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_completion.return_value = mock_response
            
            client = LLMClient()
            client._api_keys = {provider: f"{provider}_key"}
            
            messages = [{"role": "user", "content": f"Test {provider}"}]
            response = client.chat(messages)
            
            # Verify correct model format
            call_args = mock_completion.call_args[1]
            expected_model = f"{provider}/{model}"
            assert call_args["model"] == expected_model
            assert call_args["api_key"] == f"{provider}_key"


@pytest.mark.asyncio
async def test_llm_client_achat_with_tools():
    """Test async chat with tools."""
    from jarvis.llm.client import LLMClient, ToolDeclaration
    
    with patch('jarvis.llm.client.get_settings') as mock_settings, \
         patch('jarvis.llm.client.acompletion') as mock_acompletion:
        
        mock_settings.return_value.llm_provider = "openai"
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_acompletion.return_value = mock_response
        
        client = LLMClient()
        client._api_keys = {"openai": "test_key"}
        
        tools = [
            ToolDeclaration(
                name="test_tool",
                description="Test tool",
                parameters={"type": "object"}
            )
        ]
        
        messages = [{"role": "user", "content": "Use tool"}]
        response = await client.achat(messages, tools=tools)
        
        # Verify tools were included
        call_args = mock_acompletion.call_args[1]
        assert "tools" in call_args
        assert len(call_args["tools"]) == 1


def test_llm_client_edge_cases():
    """Test edge cases and boundary conditions."""
    from jarvis.llm.client import LLMClient
    
    with patch('jarvis.llm.client.get_settings') as mock_settings, \
         patch('jarvis.llm.client.completion') as mock_completion:
        
        mock_settings.return_value.llm_provider = "gemini"
        
        # Test empty messages
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_completion.return_value = mock_response
        
        client = LLMClient()
        client._api_keys = {"gemini": "test_key"}
        
        # Empty messages list
        response = client.chat([])
        assert response is not None
        
        # Messages with empty content
        response = client.chat([{"role": "user", "content": ""}])
        assert response is not None


@pytest.mark.asyncio
async def test_llm_client_stream_edge_cases():
    """Test streaming edge cases."""
    from jarvis.llm.client import LLMClient
    
    with patch('jarvis.llm.client.get_settings') as mock_settings, \
         patch('jarvis.llm.client.acompletion') as mock_acompletion:
        
        mock_settings.return_value.llm_provider = "openai"
        
        # Test empty stream
        async def mock_empty_stream():
            return
            yield  # Empty generator
        
        mock_acompletion.return_value = mock_empty_stream()
        
        client = LLMClient()
        client._api_keys = {"openai": "test_key"}
        
        messages = [{"role": "user", "content": "Test"}]
        
        chunks = []
        async for chunk in client.achat_stream(messages):
            chunks.append(chunk)
        
        assert len(chunks) == 0
