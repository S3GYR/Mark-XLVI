"""Improved tests for LLM client to increase coverage."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
from typing import Any


def test_llm_client_import():
    """Test that LLM client module imports correctly."""
    try:
        from jarvis.llm.client import LLMClient
        assert LLMClient is not None
    except ImportError:
        pytest.fail("Failed to import LLMClient")


@pytest.mark.asyncio
async def test_llm_client_initialization():
    """Test LLMClient initialization."""
    with patch('jarvis.llm.client.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        mock_settings.return_value.llm_api_key = "test-key"
        
        from jarvis.llm.client import LLMClient
        
        client = LLMClient()
        
        assert client is not None
        assert client.model == "test-model"
        assert client.temperature == 0.7
        assert client.max_tokens == 1000


@pytest.mark.asyncio
async def test_llm_client_generate_response():
    """Test LLMClient generate_response method."""
    with patch('jarvis.llm.client.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        mock_settings.return_value.llm_api_key = "test-key"
        
        with patch('litellm.completion') as mock_completion:
            mock_response = {
                "choices": [
                    {"message": {"content": "Test response"}}
                ]
            }
            mock_completion.return_value = mock_response
            
            from jarvis.llm.client import LLMClient
            
            client = LLMClient()
            result = await client.generate_response("Hello")
            
            assert result == "Test response"
            mock_completion.assert_called_once()


@pytest.mark.asyncio
async def test_llm_client_generate_response_with_context():
    """Test LLMClient generate_response with context."""
    with patch('jarvis.llm.client.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        mock_settings.return_value.llm_api_key = "test-key"
        
        with patch('litellm.completion') as mock_completion:
            mock_response = {
                "choices": [
                    {"message": {"content": "Contextual response"}}
                ]
            }
            mock_completion.return_value = mock_response
            
            from jarvis.llm.client import LLMClient
            
            client = LLMClient()
            context = ["Previous message", "Another message"]
            result = await client.generate_response("Hello", context=context)
            
            assert result == "Contextual response"
            mock_completion.assert_called_once()


@pytest.mark.asyncio
async def test_llm_client_error_handling():
    """Test LLMClient error handling."""
    with patch('jarvis.llm.client.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        mock_settings.return_value.llm_api_key = "test-key"
        
        with patch('litellm.completion') as mock_completion:
            mock_completion.side_effect = Exception("API error")
            
            from jarvis.llm.client import LLMClient
            
            client = LLMClient()
            
            with pytest.raises(Exception, match="API error"):
                await client.generate_response("Hello")


@pytest.mark.asyncio
async def test_llm_client_empty_response():
    """Test LLMClient handles empty response."""
    with patch('jarvis.llm.client.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        mock_settings.return_value.llm_api_key = "test-key"
        
        with patch('litellm.completion') as mock_completion:
            mock_response = {
                "choices": [
                    {"message": {"content": ""}}
                ]
            }
            mock_completion.return_value = mock_response
            
            from jarvis.llm.client import LLMClient
            
            client = LLMClient()
            result = await client.generate_response("Hello")
            
            assert result == ""


@pytest.mark.asyncio
async def test_llm_client_no_choices():
    """Test LLMClient handles response with no choices."""
    with patch('jarvis.llm.client.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        mock_settings.return_value.llm_api_key = "test-key"
        
        with patch('litellm.completion') as mock_completion:
            mock_response = {"choices": []}
            mock_completion.return_value = mock_response
            
            from jarvis.llm.client import LLMClient
            
            client = LLMClient()
            
            with pytest.raises(Exception):
                await client.generate_response("Hello")


@pytest.mark.asyncio
async def test_llm_client_malformed_response():
    """Test LLMClient handles malformed response."""
    with patch('jarvis.llm.client.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        mock_settings.return_value.llm_api_key = "test-key"
        
        with patch('litellm.completion') as mock_completion:
            mock_response = {"choices": [{"message": {}}]}
            mock_completion.return_value = mock_response
            
            from jarvis.llm.client import LLMClient
            
            client = LLMClient()
            
            with pytest.raises(Exception):
                await client.generate_response("Hello")


@pytest.mark.asyncio
async def test_llm_client_long_input():
    """Test LLMClient handles long input."""
    with patch('jarvis.llm.client.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        mock_settings.return_value.llm_api_key = "test-key"
        
        with patch('litellm.completion') as mock_completion:
            mock_response = {
                "choices": [
                    {"message": {"content": "Long input response"}}
                ]
            }
            mock_completion.return_value = mock_response
            
            from jarvis.llm.client import LLMClient
            
            client = LLMClient()
            long_input = "This is a very long input " * 100
            result = await client.generate_response(long_input)
            
            assert result == "Long input response"
            mock_completion.assert_called_once()


@pytest.mark.asyncio
async def test_llm_client_special_characters():
    """Test LLMClient handles special characters."""
    with patch('jarvis.llm.client.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        mock_settings.return_value.llm_api_key = "test-key"
        
        with patch('litellm.completion') as mock_completion:
            mock_response = {
                "choices": [
                    {"message": {"content": "Special chars response"}}
                ]
            }
            mock_completion.return_value = mock_response
            
            from jarvis.llm.client import LLMClient
            
            client = LLMClient()
            special_input = "Test with émojis 🎉 and special chars: @#$%^&*()"
            result = await client.generate_response(special_input)
            
            assert result == "Special chars response"
            mock_completion.assert_called_once()


@pytest.mark.asyncio
async def test_llm_client_concurrent_requests():
    """Test LLMClient handles concurrent requests."""
    with patch('jarvis.llm.client.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        mock_settings.return_value.llm_api_key = "test-key"
        
        with patch('litellm.completion') as mock_completion:
            mock_response = {
                "choices": [
                    {"message": {"content": "Concurrent response"}}
                ]
            }
            mock_completion.return_value = mock_response
            
            from jarvis.llm.client import LLMClient
            
            client = LLMClient()
            
            # Run multiple requests concurrently
            tasks = [
                client.generate_response(f"Request {i}")
                for i in range(5)
            ]
            
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 5
            assert all(result == "Concurrent response" for result in results)


@pytest.mark.asyncio
async def test_llm_client_temperature_parameter():
    """Test LLMClient passes temperature parameter correctly."""
    with patch('jarvis.llm.client.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.1  # Low temperature
        mock_settings.return_value.llm_max_tokens = 1000
        mock_settings.return_value.llm_api_key = "test-key"
        
        with patch('litellm.completion') as mock_completion:
            mock_response = {
                "choices": [
                    {"message": {"content": "Low temp response"}}
                ]
            }
            mock_completion.return_value = mock_response
            
            from jarvis.llm.client import LLMClient
            
            client = LLMClient()
            await client.generate_response("Hello")
            
            # Check that temperature was passed correctly
            call_args = mock_completion.call_args[1]
            assert call_args.get('temperature') == 0.1


@pytest.mark.asyncio
async def test_llm_client_max_tokens_parameter():
    """Test LLMClient passes max_tokens parameter correctly."""
    with patch('jarvis.llm.client.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 500  # Limited tokens
        mock_settings.return_value.llm_api_key = "test-key"
        
        with patch('litellm.completion') as mock_completion:
            mock_response = {
                "choices": [
                    {"message": {"content": "Limited response"}}
                ]
            }
            mock_completion.return_value = mock_response
            
            from jarvis.llm.client import LLMClient
            
            client = LLMClient()
            await client.generate_response("Hello")
            
            # Check that max_tokens was passed correctly
            call_args = mock_completion.call_args[1]
            assert call_args.get('max_tokens') == 500


@pytest.mark.asyncio
async def test_llm_client_model_parameter():
    """Test LLMClient passes model parameter correctly."""
    with patch('jarvis.llm.client.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "gpt-4"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        mock_settings.return_value.llm_api_key = "test-key"
        
        with patch('litellm.completion') as mock_completion:
            mock_response = {
                "choices": [
                    {"message": {"content": "GPT-4 response"}}
                ]
            }
            mock_completion.return_value = mock_response
            
            from jarvis.llm.client import LLMClient
            
            client = LLMClient()
            await client.generate_response("Hello")
            
            # Check that model was passed correctly
            call_args = mock_completion.call_args[1]
            assert call_args.get('model') == "gpt-4"


@pytest.mark.asyncio
async def test_llm_client_api_key_parameter():
    """Test LLMClient passes API key parameter correctly."""
    with patch('jarvis.llm.client.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        mock_settings.return_value.llm_api_key = "secret-api-key"
        
        with patch('litellm.completion') as mock_completion:
            mock_response = {
                "choices": [
                    {"message": {"content": "Authenticated response"}}
                ]
            }
            mock_completion.return_value = mock_response
            
            from jarvis.llm.client import LLMClient
            
            client = LLMClient()
            await client.generate_response("Hello")
            
            # Check that API key was passed correctly
            call_args = mock_completion.call_args[1]
            assert call_args.get('api_key') == "secret-api-key"


@pytest.mark.asyncio
async def test_llm_client_context_formatting():
    """Test LLMClient formats context correctly."""
    with patch('jarvis.llm.client.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        mock_settings.return_value.llm_api_key = "test-key"
        
        with patch('litellm.completion') as mock_completion:
            mock_response = {
                "choices": [
                    {"message": {"content": "Formatted response"}}
                ]
            }
            mock_completion.return_value = mock_response
            
            from jarvis.llm.client import LLMClient
            
            client = LLMClient()
            context = ["User: Hello", "Assistant: Hi there"]
            await client.generate_response("How are you?", context=context)
            
            # Check that context was included in the messages
            call_args = mock_completion.call_args[1]
            messages = call_args.get('messages', [])
            assert len(messages) >= 3  # context + current message


@pytest.mark.asyncio
async def test_llm_client_empty_context():
    """Test LLMClient handles empty context."""
    with patch('jarvis.llm.client.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        mock_settings.return_value.llm_api_key = "test-key"
        
        with patch('litellm.completion') as mock_completion:
            mock_response = {
                "choices": [
                    {"message": {"content": "No context response"}}
                ]
            }
            mock_completion.return_value = mock_response
            
            from jarvis.llm.client import LLMClient
            
            client = LLMClient()
            await client.generate_response("Hello", context=[])
            
            # Should still work with empty context
            mock_completion.assert_called_once()


@pytest.mark.asyncio
async def test_llm_client_null_context():
    """Test LLMClient handles None context."""
    with patch('jarvis.llm.client.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        mock_settings.return_value.llm_api_key = "test-key"
        
        with patch('litellm.completion') as mock_completion:
            mock_response = {
                "choices": [
                    {"message": {"content": "Null context response"}}
                ]
            }
            mock_completion.return_value = mock_response
            
            from jarvis.llm.client import LLMClient
            
            client = LLMClient()
            await client.generate_response("Hello", context=None)
            
            # Should still work with None context
            mock_completion.assert_called_once()


@pytest.mark.asyncio
async def test_llm_client_rate_limit_handling():
    """Test LLMClient handles rate limiting."""
    with patch('jarvis.llm.client.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        mock_settings.return_value.llm_api_key = "test-key"
        
        with patch('litellm.completion') as mock_completion:
            # Simulate rate limit error
            from litellm import RateLimitError
            mock_completion.side_effect = RateLimitError("Rate limit exceeded")
            
            from jarvis.llm.client import LLMClient
            
            client = LLMClient()
            
            with pytest.raises(RateLimitError, match="Rate limit exceeded"):
                await client.generate_response("Hello")
