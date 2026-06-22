"""Phase 2 LLM Client tests for comprehensive coverage (>75%)."""

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


def test_llm_client_initialization_with_custom_settings():
    """Test LLMClient initialization with custom settings."""
    from jarvis.llm.client import LLMClient
    from jarvis.config.settings import Settings
    
    custom_settings = Settings(
        llm_provider="openai",
        llm_model="gpt-4",
        llm_temperature=0.5
    )
    
    with patch('jarvis.llm.client.get_settings') as mock_settings:
        client = LLMClient(custom_settings)
        
        assert client.settings == custom_settings


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
        assert client._api_key_for_model("openai/gpt-4") == "openai_key"
        assert client._api_key_for_model("anthropic/claude-3") == "anthropic_key"
        assert client._api_key_for_model("gemini/gemini-pro") == "gemini_key"
        
        # Test model without provider prefix (uses default provider)
        assert client._api_key_for_model("gpt-4") == "gemini_key"
        
        # Test unknown provider
        assert client._api_key_for_model("unknown/model") is None


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


def test_llm_client_normalize_tool_calls():
    """Test tool call normalization."""
    from jarvis.llm.client import LLMClient
    from jarvis.llm.client import ToolCall
    
    client = LLMClient()
    
    # Test None tool calls
    assert client._normalize_tool_calls(None) == []
    
    # Test empty tool calls
    assert client._normalize_tool_calls([]) == []
    
    # Test OpenAI format
    openai_tool_calls = [
        {
            "id": "call_123",
            "function": {
                "name": "test_tool",
                "arguments": '{"param": "value"}'
            }
        }
    ]
    
    normalized = client._normalize_tool_calls(openai_tool_calls)
    assert len(normalized) == 1
    assert normalized[0].id == "call_123"
    assert normalized[0].name == "test_tool"
    assert normalized[0].arguments == {"param": "value"}


def test_llm_client_normalize_response():
    """Test response normalization."""
    from jarvis.llm.client import LLMClient
    from jarvis.llm.client import LLMResponse
    
    client = LLMClient()
    
    # Test minimal response
    minimal_response = {
        "choices": [
            {
                "message": {"content": "Test response"},
                "finish_reason": "stop"
            }
        ],
        "model": "test-model"
    }
    
    normalized = client._normalize_response(minimal_response)
    assert isinstance(normalized, LLMResponse)
    assert normalized.content == "Test response"
    assert normalized.tool_calls == []
    assert normalized.finish_reason == "stop"
    assert normalized.model == "test-model"
    assert normalized.usage is None
    
    # Test full response with tool calls and usage
    full_response = {
        "choices": [
            {
                "message": {
                    "content": "Response with tools",
                    "tool_calls": [
                        {
                            "id": "call_123",
                            "function": {
                                "name": "test_tool",
                                "arguments": '{"param": "value"}'
                            }
                        }
                    ]
                },
                "finish_reason": "tool_calls"
            }
        ],
        "model": "test-model",
        "usage": {"prompt_tokens": 10, "completion_tokens": 20}
    }
    
    normalized = client._normalize_response(full_response)
    assert normalized.content == "Response with tools"
    assert len(normalized.tool_calls) == 1
    assert normalized.tool_calls[0].id == "call_123"
    assert normalized.finish_reason == "tool_calls"
    assert normalized.usage == {"prompt_tokens": 10, "completion_tokens": 20}


@pytest.mark.asyncio
async def test_llm_client_generate_response_success():
    """Test successful response generation."""
    from jarvis.llm.client import LLMClient
    
    with patch('jarvis.llm.client.get_settings') as mock_settings, \
         patch('jarvis.llm.client.acompletion') as mock_acompletion:
        
        mock_settings.return_value.llm_provider = "gemini"
        mock_settings.return_value.llm_model = "gemini-2.0-flash"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        
        mock_response = {
            "choices": [
                {
                    "message": {"content": "Test response"},
                    "finish_reason": "stop"
                }
            ],
            "model": "gemini-2.0-flash"
        }
        mock_acompletion.return_value = mock_response
        
        client = LLMClient()
        client._api_keys = {"gemini": "test_key"}
        
        response = await client.generate_response("Test prompt")
        
        assert response.content == "Test response"
        assert response.model == "gemini-2.0-flash"
        assert response.finish_reason == "stop"
        assert response.tool_calls == []
        
        # Verify API call was made correctly
        mock_acompletion.assert_called_once()
        call_args = mock_acompletion.call_args[1]
        assert call_args["model"] == "gemini/gemini-2.0-flash"
        assert call_args["messages"] == [{"role": "user", "content": "Test prompt"}]
        assert call_args["temperature"] == 0.7
        assert call_args["max_tokens"] == 1000


@pytest.mark.asyncio
async def test_llm_client_generate_response_with_tools():
    """Test response generation with tools."""
    from jarvis.llm.client import LLMClient, ToolDeclaration
    
    with patch('jarvis.llm.client.get_settings') as mock_settings, \
         patch('jarvis.llm.client.acompletion') as mock_acompletion:
        
        mock_settings.return_value.llm_provider = "openai"
        mock_settings.return_value.llm_model = "gpt-4"
        
        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": "I'll use a tool",
                        "tool_calls": [
                            {
                                "id": "call_123",
                                "function": {
                                    "name": "test_tool",
                                    "arguments": '{"param": "value"}'
                                }
                            }
                        ]
                    },
                    "finish_reason": "tool_calls"
                }
            ],
            "model": "gpt-4"
        }
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
        
        response = await client.generate_response("Use a tool", tools=tools)
        
        assert response.content == "I'll use a tool"
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].name == "test_tool"
        assert response.finish_reason == "tool_calls"
        
        # Verify tools were included in API call
        call_args = mock_acompletion.call_args[1]
        assert "tools" in call_args
        assert len(call_args["tools"]) == 1


@pytest.mark.asyncio
async def test_llm_client_generate_response_with_context():
    """Test response generation with conversation context."""
    from jarvis.llm.client import LLMClient
    
    with patch('jarvis.llm.client.get_settings') as mock_settings, \
         patch('jarvis.llm.client.acompletion') as mock_acompletion:
        
        mock_settings.return_value.llm_provider = "anthropic"
        mock_settings.return_value.llm_model = "claude-3"
        
        mock_response = {
            "choices": [
                {
                    "message": {"content": "Contextual response"},
                    "finish_reason": "stop"
                }
            ],
            "model": "claude-3"
        }
        mock_acompletion.return_value = mock_response
        
        client = LLMClient()
        client._api_keys = {"anthropic": "test_key"}
        
        context = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        response = await client.generate_response("How are you?", context=context)
        
        assert response.content == "Contextual response"
        
        # Verify context was included
        call_args = mock_acompletion.call_args[1]
        expected_messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ]
        assert call_args["messages"] == expected_messages


@pytest.mark.asyncio
async def test_llm_client_generate_response_no_api_key():
    """Test response generation when no API key is available."""
    from jarvis.llm.client import LLMClient
    
    with patch('jarvis.llm.client.get_settings') as mock_settings:
        mock_settings.return_value.llm_provider = "gemini"
        
        client = LLMClient()
        # No API keys loaded
        
        with pytest.raises(ValueError, match="No API key found"):
            await client.generate_response("Test prompt")


@pytest.mark.asyncio
async def test_llm_client_generate_response_api_error():
    """Test response generation with API error."""
    from jarvis.llm.client import LLMClient
    import litellm
    
    with patch('jarvis.llm.client.get_settings') as mock_settings, \
         patch('jarvis.llm.client.acompletion') as mock_acompletion:
        
        mock_settings.return_value.llm_provider = "openai"
        
        # Simulate API error
        mock_acompletion.side_effect = litellm.APIConnectionError("API connection failed")
        
        client = LLMClient()
        client._api_keys = {"openai": "test_key"}
        
        with pytest.raises(litellm.APIConnectionError):
            await client.generate_response("Test prompt")


@pytest.mark.asyncio
async def test_llm_client_generate_response_rate_limit():
    """Test response generation with rate limiting."""
    from jarvis.llm.client import LLMClient
    import litellm
    
    with patch('jarvis.llm.client.get_settings') as mock_settings, \
         patch('jarvis.llm.client.acompletion') as mock_acompletion:
        
        mock_settings.return_value.llm_provider = "anthropic"
        
        # Simulate rate limit error
        mock_acompletion.side_effect = litellm.RateLimitError("Rate limit exceeded")
        
        client = LLMClient()
        client._api_keys = {"anthropic": "test_key"}
        
        with pytest.raises(litellm.RateLimitError):
            await client.generate_response("Test prompt")


@pytest.mark.asyncio
async def test_llm_client_generate_response_timeout():
    """Test response generation with timeout."""
    from jarvis.llm.client import LLMClient
    import litellm
    
    with patch('jarvis.llm.client.get_settings') as mock_settings, \
         patch('jarvis.llm.client.acompletion') as mock_acompletion:
        
        mock_settings.return_value.llm_provider = "gemini"
        
        # Simulate timeout
        mock_acompletion.side_effect = litellm.Timeout("Request timeout")
        
        client = LLMClient()
        client._api_keys = {"gemini": "test_key"}
        
        with pytest.raises(litellm.Timeout):
            await client.generate_response("Test prompt")


@pytest.mark.asyncio
async def test_llm_client_generate_response_invalid_response():
    """Test response generation with invalid API response."""
    from jarvis.llm.client import LLMClient
    
    with patch('jarvis.llm.client.get_settings') as mock_settings, \
         patch('jarvis.llm.client.acompletion') as mock_acompletion:
        
        mock_settings.return_value.llm_provider = "openai"
        
        # Simulate invalid response
        mock_acompletion.return_value = {"invalid": "response"}
        
        client = LLMClient()
        client._api_keys = {"openai": "test_key"}
        
        with pytest.raises(ValueError, match="Invalid response format"):
            await client.generate_response("Test prompt")


@pytest.mark.asyncio
async def test_llm_client_generate_response_empty_choices():
    """Test response generation with empty choices."""
    from jarvis.llm.client import LLMClient
    
    with patch('jarvis.llm.client.get_settings') as mock_settings, \
         patch('jarvis.llm.client.acompletion') as mock_acompletion:
        
        mock_settings.return_value.llm_provider = "gemini"
        
        # Simulate empty choices
        mock_acompletion.return_value = {"choices": []}
        
        client = LLMClient()
        client._api_keys = {"gemini": "test_key"}
        
        with pytest.raises(ValueError, match="No response from LLM"):
            await client.generate_response("Test prompt")


@pytest.mark.asyncio
async def test_llm_client_generate_response_concurrent():
    """Test concurrent response generation."""
    from jarvis.llm.client import LLMClient
    
    with patch('jarvis.llm.client.get_settings') as mock_settings, \
         patch('jarvis.llm.client.acompletion') as mock_acompletion:
        
        mock_settings.return_value.llm_provider = "openai"
        
        mock_response = {
            "choices": [
                {
                    "message": {"content": "Concurrent response"},
                    "finish_reason": "stop"
                }
            ],
            "model": "gpt-4"
        }
        mock_acompletion.return_value = mock_response
        
        client = LLMClient()
        client._api_keys = {"openai": "test_key"}
        
        # Create concurrent requests
        tasks = [
            client.generate_response(f"Concurrent request {i}")
            for i in range(5)
        ]
        
        responses = await asyncio.gather(*tasks)
        
        assert len(responses) == 5
        assert all(r.content == "Concurrent response" for r in responses)
        assert mock_acompletion.call_count == 5


@pytest.mark.asyncio
async def test_llm_client_generate_response_streaming():
    """Test streaming response generation."""
    from jarvis.llm.client import LLMClient
    
    with patch('jarvis.llm.client.get_settings') as mock_settings, \
         patch('jarvis.llm.client.acompletion') as mock_acompletion:
        
        mock_settings.return_value.llm_provider = "anthropic"
        
        # Simulate streaming response
        async def mock_stream():
            chunks = [
                {"choices": [{"delta": {"content": "Hello"}}]},
                {"choices": [{"delta": {"content": " world"}}]},
                {"choices": [{"finish_reason": "stop"}]}
            ]
            for chunk in chunks:
                yield chunk
        
        mock_acompletion.return_value = mock_stream()
        
        client = LLMClient()
        client._api_keys = {"anthropic": "test_key"}
        
        stream = client.generate_response("Stream test", stream=True)
        
        chunks = []
        async for chunk in stream:
            chunks.append(chunk)
        
        assert len(chunks) == 3
        assert chunks[0]["choices"][0]["delta"]["content"] == "Hello"
        assert chunks[1]["choices"][0]["delta"]["content"] == " world"
        assert chunks[2]["choices"][0]["finish_reason"] == "stop"


@pytest.mark.asyncio
async def test_llm_client_generate_response_with_system_prompt():
    """Test response generation with system prompt."""
    from jarvis.llm.client import LLMClient
    
    with patch('jarvis.llm.client.get_settings') as mock_settings, \
         patch('jarvis.llm.client.acompletion') as mock_acompletion:
        
        mock_settings.return_value.llm_provider = "openai"
        
        mock_response = {
            "choices": [
                {
                    "message": {"content": "System-aware response"},
                    "finish_reason": "stop"
                }
            ],
            "model": "gpt-4"
        }
        mock_acompletion.return_value = mock_response
        
        client = LLMClient()
        client._api_keys = {"openai": "test_key"}
        
        context = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello"}
        ]
        
        response = await client.generate_response("Hello", context=context)
        
        assert response.content == "System-aware response"
        
        # Verify system prompt was included
        call_args = mock_acompletion.call_args[1]
        expected_messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello"}
        ]
        assert call_args["messages"] == expected_messages


@pytest.mark.asyncio
async def test_llm_client_generate_response_different_providers():
    """Test response generation with different providers."""
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
             patch('jarvis.llm.client.acompletion') as mock_acompletion:
            
            mock_settings.return_value.llm_provider = provider
            mock_settings.return_value.llm_model = model
            
            mock_response = {
                "choices": [
                    {
                        "message": {"content": f"Response from {provider}"},
                        "finish_reason": "stop"
                    }
                ],
                "model": model
            }
            mock_acompletion.return_value = mock_response
            
            client = LLMClient()
            client._api_keys = {provider: f"{provider}_key"}
            
            response = await client.generate_response(f"Test {provider}")
            
            assert response.content == f"Response from {provider}"
            assert response.model == model
            
            # Verify correct model format
            call_args = mock_acompletion.call_args[1]
            expected_model = f"{provider}/{model}"
            assert call_args["model"] == expected_model


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


def test_llm_client_class_structure():
    """Test LLMClient class structure."""
    from jarvis.llm.client import LLMClient
    import inspect
    
    # Check class has expected methods
    assert hasattr(LLMClient, '__init__')
    assert hasattr(LLMClient, '_load_api_keys')
    assert hasattr(LLMClient, '_api_key_for_model')
    assert hasattr(LLMClient, '_get_model')
    assert hasattr(LLMClient, '_normalize_tools')
    assert hasattr(LLMClient, '_normalize_tool_calls')
    assert hasattr(LLMClient, '_normalize_response')
    assert hasattr(LLMClient, 'generate_response')
    
    # Check async methods
    assert inspect.iscoroutinefunction(LLMClient.generate_response)


@pytest.mark.asyncio
async def test_llm_client_error_handling_malformed_tool_calls():
    """Test error handling with malformed tool calls."""
    from jarvis.llm.client import LLMClient
    
    client = LLMClient()
    
    # Test malformed tool calls
    malformed_tool_calls = [
        {
            "id": "call_123",
            "function": {
                "name": "test_tool",
                "arguments": "invalid json"  # Not valid JSON
            }
        }
    ]
    
    # Should handle gracefully
    normalized = client._normalize_tool_calls(malformed_tool_calls)
    assert len(normalized) == 1
    assert normalized[0].id == "call_123"
    assert normalized[0].name == "test_tool"
    # Arguments should be empty dict due to JSON parsing error
    assert normalized[0].arguments == {}


@pytest.mark.asyncio
async def test_llm_client_generate_response_large_input():
    """Test response generation with large input."""
    from jarvis.llm.client import LLMClient
    
    with patch('jarvis.llm.client.get_settings') as mock_settings, \
         patch('jarvis.llm.client.acompletion') as mock_acompletion:
        
        mock_settings.return_value.llm_provider = "gemini"
        
        mock_response = {
            "choices": [
                {
                    "message": {"content": "Large input handled"},
                    "finish_reason": "stop"
                }
            ],
            "model": "gemini-2.0-flash"
        }
        mock_acompletion.return_value = mock_response
        
        client = LLMClient()
        client._api_keys = {"gemini": "test_key"}
        
        # Create large input (10,000 characters)
        large_input = "This is a large input. " * 500
        
        response = await client.generate_response(large_input)
        
        assert response.content == "Large input handled"
        mock_acompletion.assert_called_once()


@pytest.mark.asyncio
async def test_llm_client_generate_response_special_characters():
    """Test response generation with special characters."""
    from jarvis.llm.client import LLMClient
    
    with patch('jarvis.llm.client.get_settings') as mock_settings, \
         patch('jarvis.llm.client.acompletion') as mock_acompletion:
        
        mock_settings.return_value.llm_provider = "openai"
        
        mock_response = {
            "choices": [
                {
                    "message": {"content": "Special chars handled: émojis 🎉 and symbols @#$%"},
                    "finish_reason": "stop"
                }
            ],
            "model": "gpt-4"
        }
        mock_acompletion.return_value = mock_response
        
        client = LLMClient()
        client._api_keys = {"openai": "test_key"}
        
        special_input = "Test with émojis 🎉 and symbols: @#$%^&*()[]{}|\\:;<>?,./"
        
        response = await client.generate_response(special_input)
        
        assert "émojis 🎉" in response.content
        assert "@#$%" in response.content
