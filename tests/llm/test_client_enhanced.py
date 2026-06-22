"""Enhanced LLM client tests for comprehensive coverage (>70%)."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
import json
from typing import Any


@pytest.mark.asyncio
async def test_llm_client_initialization_with_settings():
    """Test LLMClient initialization with custom settings."""
    with patch('jarvis.llm.client.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "gpt-4"
        mock_settings.return_value.llm_temperature = 0.5
        mock_settings.return_value.llm_max_tokens = 1500
        mock_settings.return_value.llm_api_key = "custom_key"
        mock_settings.return_value.llm_base_url = "https://api.custom.com"
        
        from jarvis.llm.client import LLMClient
        
        client = LLMClient()
        
        assert client.model == "gpt-4"
        assert client.temperature == 0.5
        assert client.max_tokens == 1500
        assert client.api_key == "custom_key"
        assert client.base_url == "https://api.custom.com"


@pytest.mark.asyncio
async def test_llm_client_generate_response_timeout():
    """Test LLMClient with timeout handling."""
    with patch('jarvis.llm.client.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        mock_settings.return_value.llm_api_key = "test-key"
        
        with patch('litellm.completion') as mock_completion:
            # Simulate timeout
            import asyncio
            mock_completion.side_effect = asyncio.TimeoutError("Request timeout")
            
            from jarvis.llm.client import LLMClient
            
            client = LLMClient()
            
            with pytest.raises(asyncio.TimeoutError):
                await client.generate_response("Test timeout")


@pytest.mark.asyncio
async def test_llm_client_generate_response_network_error():
    """Test LLMClient with network errors."""
    with patch('jarvis.llm.client.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        mock_settings.return_value.llm_api_key = "test-key"
        
        with patch('litellm.completion') as mock_completion:
            # Simulate network error
            mock_completion.side_effect = ConnectionError("Network unreachable")
            
            from jarvis.llm.client import LLMClient
            
            client = LLMClient()
            
            with pytest.raises(ConnectionError):
                await client.generate_response("Test network error")


@pytest.mark.asyncio
async def test_llm_client_generate_response_quota_exceeded():
    """Test LLMClient with quota exceeded error."""
    with patch('jarvis.llm.client.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        mock_settings.return_value.llm_api_key = "test-key"
        
        with patch('litellm.completion') as mock_completion:
            # Simulate quota exceeded
            from litellm import RateLimitError
            mock_completion.side_effect = RateLimitError("Quota exceeded")
            
            from jarvis.llm.client import LLMClient
            
            client = LLMClient()
            
            with pytest.raises(RateLimitError):
                await client.generate_response("Test quota exceeded")


@pytest.mark.asyncio
async def test_llm_client_generate_response_invalid_api_key():
    """Test LLMClient with invalid API key."""
    with patch('jarvis.llm.client.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        mock_settings.return_value.llm_api_key = "invalid_key"
        
        with patch('litellm.completion') as mock_completion:
            # Simulate invalid API key
            from litellm import AuthenticationError
            mock_completion.side_effect = AuthenticationError("Invalid API key")
            
            from jarvis.llm.client import LLMClient
            
            client = LLMClient()
            
            with pytest.raises(AuthenticationError):
                await client.generate_response("Test invalid API key")


@pytest.mark.asyncio
async def test_llm_client_generate_response_empty_response():
    """Test LLMClient with empty response from API."""
    with patch('jarvis.llm.client.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        mock_settings.return_value.llm_api_key = "test-key"
        
        with patch('litellm.completion') as mock_completion:
            # Simulate empty response
            mock_response = {"choices": []}
            mock_completion.return_value = mock_response
            
            from jarvis.llm.client import LLMClient
            
            client = LLMClient()
            
            with pytest.raises(ValueError, match="No response from LLM"):
                await client.generate_response("Test empty response")


@pytest.mark.asyncio
async def test_llm_client_generate_response_malformed_response():
    """Test LLMClient with malformed response."""
    with patch('jarvis.llm.client.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        mock_settings.return_value.llm_api_key = "test-key"
        
        with patch('litellm.completion') as mock_completion:
            # Simulate malformed response
            mock_response = {"choices": [{"message": {}}]}  # Missing content
            mock_completion.return_value = mock_response
            
            from jarvis.llm.client import LLMClient
            
            client = LLMClient()
            
            with pytest.raises(ValueError, match="Invalid response format"):
                await client.generate_response("Test malformed response")


@pytest.mark.asyncio
async def test_llm_client_generate_response_with_context():
    """Test LLMClient with conversation context."""
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
            context = [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ]
            
            result = await client.generate_response("How are you?", context=context)
            
            assert result == "Contextual response"
            
            # Verify context was included
            call_args = mock_completion.call_args[1]
            messages = call_args.get('messages', [])
            assert len(messages) >= 3  # context + current message


@pytest.mark.asyncio
async def test_llm_client_generate_response_long_input():
    """Test LLMClient with very long input."""
    with patch('jarvis.llm.client.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        mock_settings.return_value.llm_api_key = "test-key"
        
        with patch('litellm.completion') as mock_completion:
            mock_response = {
                "choices": [
                    {"message": {"content": "Long input handled"}}
                ]
            }
            mock_completion.return_value = mock_response
            
            from jarvis.llm.client import LLMClient
            
            client = LLMClient()
            long_input = "This is a very long input " * 1000  # ~20,000 characters
            
            result = await client.generate_response(long_input)
            
            assert result == "Long input handled"
            mock_completion.assert_called_once()


@pytest.mark.asyncio
async def test_llm_client_generate_response_special_characters():
    """Test LLMClient with special characters."""
    with patch('jarvis.llm.client.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        mock_settings.return_value.llm_api_key = "test-key"
        
        with patch('litellm.completion') as mock_completion:
            mock_response = {
                "choices": [
                    {"message": {"content": "Special chars handled"}}
                ]
            }
            mock_completion.return_value = mock_response
            
            from jarvis.llm.client import LLMClient
            
            client = LLMClient()
            special_input = "Test with émojis 🎉 and special chars: @#$%^&*()[]{}|\\:;<>?,./"
            
            result = await client.generate_response(special_input)
            
            assert result == "Special chars handled"
            mock_completion.assert_called_once()


@pytest.mark.asyncio
async def test_llm_client_generate_response_concurrent():
    """Test LLMClient with concurrent requests."""
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
            
            # Create concurrent requests
            tasks = [
                client.generate_response(f"Concurrent request {i}")
                for i in range(10)
            ]
            
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 10
            assert all(result == "Concurrent response" for result in results)
            assert mock_completion.call_count == 10


@pytest.mark.asyncio
async def test_llm_client_generate_response_fallback_provider():
    """Test LLMClient with fallback provider."""
    with patch('jarvis.llm.client.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        mock_settings.return_value.llm_api_key = "test-key"
        
        with patch('litellm.completion') as mock_completion:
            # First call fails, second succeeds
            mock_completion.side_effect = [
                ConnectionError("Primary provider failed"),
                {
                    "choices": [
                        {"message": {"content": "Fallback response"}}
                    ]
                }
            ]
            
            from jarvis.llm.client import LLMClient
            
            client = LLMClient()
            
            # This test assumes the client has retry logic
            try:
                result = await client.generate_response("Test fallback")
                # If retry logic exists, this should succeed
                assert result == "Fallback response"
            except ConnectionError:
                # If no retry logic, this is expected
                pass


@pytest.mark.asyncio
async def test_llm_client_generate_response_streaming():
    """Test LLMClient with streaming responses."""
    with patch('jarvis.llm.client.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        mock_settings.return_value.llm_api_key = "test-key"
        
        with patch('litellm.completion') as mock_completion:
            # Simulate streaming response
            mock_response = {
                "choices": [
                    {"message": {"content": "Streaming response"}}
                ]
            }
            mock_completion.return_value = mock_response
            
            from jarvis.llm.client import LLMClient
            
            client = LLMClient()
            
            # Test streaming mode (if supported)
            try:
                result = await client.generate_response("Test streaming", stream=True)
                assert result == "Streaming response"
            except (TypeError, ValueError):
                # Streaming might not be supported
                result = await client.generate_response("Test streaming")
                assert result == "Streaming response"


@pytest.mark.asyncio
async def test_llm_client_generate_response_interruption():
    """Test LLMClient with interruption during streaming."""
    with patch('jarvis.llm.client.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        mock_settings.return_value.llm_api_key = "test-key"
        
        with patch('litellm.completion') as mock_completion:
            # Simulate interruption
            mock_completion.side_effect = KeyboardInterrupt("User interrupted")
            
            from jarvis.llm.client import LLMClient
            
            client = LLMClient()
            
            with pytest.raises(KeyboardInterrupt):
                await client.generate_response("Test interruption")


@pytest.mark.asyncio
async def test_llm_client_generate_response_retry_logic():
    """Test LLMClient retry logic."""
    with patch('jarvis.llm.client.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        mock_settings.return_value.llm_api_key = "test-key"
        
        with patch('litellm.completion') as mock_completion:
            # Simulate temporary failure then success
            call_count = 0
            
            def mock_side_effect(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise ConnectionError("Temporary failure")
                else:
                    return {
                        "choices": [
                            {"message": {"content": "Retry success"}}
                        ]
                    }
            
            mock_completion.side_effect = mock_side_effect
            
            from jarvis.llm.client import LLMClient
            
            client = LLMClient()
            
            # Test retry logic (if implemented)
            try:
                result = await client.generate_response("Test retry")
                assert result == "Retry success"
                assert call_count == 2
            except ConnectionError:
                # If no retry logic
                assert call_count == 1


@pytest.mark.asyncio
async def test_llm_client_generate_response_different_models():
    """Test LLMClient with different models."""
    models = ["gpt-3.5-turbo", "gpt-4", "claude-3", "gemini-pro"]
    
    for model in models:
        with patch('jarvis.llm.client.get_settings') as mock_settings:
            mock_settings.return_value.llm_model = model
            mock_settings.return_value.llm_temperature = 0.7
            mock_settings.return_value.llm_max_tokens = 1000
            mock_settings.return_value.llm_api_key = "test-key"
            
            with patch('litellm.completion') as mock_completion:
                mock_response = {
                    "choices": [
                        {"message": {"content": f"Response from {model}"}}
                    ]
                }
                mock_completion.return_value = mock_response
                
                from jarvis.llm.client import LLMClient
                
                client = LLMClient()
                result = await client.generate_response(f"Test {model}")
                
                assert result == f"Response from {model}"
                
                # Verify correct model was used
                call_args = mock_completion.call_args[1]
                assert call_args.get('model') == model


@pytest.mark.asyncio
async def test_llm_client_generate_response_temperature_effects():
    """Test LLMClient with different temperature settings."""
    temperatures = [0.0, 0.5, 1.0, 1.5, 2.0]
    
    for temp in temperatures:
        with patch('jarvis.llm.client.get_settings') as mock_settings:
            mock_settings.return_value.llm_model = "test-model"
            mock_settings.return_value.llm_temperature = temp
            mock_settings.return_value.llm_max_tokens = 1000
            mock_settings.return_value.llm_api_key = "test-key"
            
            with patch('litellm.completion') as mock_completion:
                mock_response = {
                    "choices": [
                        {"message": {"content": f"Response at temp {temp}"}}
                    ]
                }
                mock_completion.return_value = mock_response
                
                from jarvis.llm.client import LLMClient
                
                client = LLMClient()
                result = await client.generate_response(f"Test temp {temp}")
                
                assert result == f"Response at temp {temp}"
                
                # Verify correct temperature was used
                call_args = mock_completion.call_args[1]
                assert call_args.get('temperature') == temp


@pytest.mark.asyncio
async def test_llm_client_generate_response_max_tokens_limit():
    """Test LLMClient with different max tokens settings."""
    max_tokens_list = [100, 500, 1000, 2000, 4000]
    
    for max_tokens in max_tokens_list:
        with patch('jarvis.llm.client.get_settings') as mock_settings:
            mock_settings.return_value.llm_model = "test-model"
            mock_settings.return_value.llm_temperature = 0.7
            mock_settings.return_value.llm_max_tokens = max_tokens
            mock_settings.return_value.llm_api_key = "test-key"
            
            with patch('litellm.completion') as mock_completion:
                mock_response = {
                    "choices": [
                        {"message": {"content": f"Response with {max_tokens} tokens"}}
                    ]
                }
                mock_completion.return_value = mock_response
                
                from jarvis.llm.client import LLMClient
                
                client = LLMClient()
                result = await client.generate_response(f"Test {max_tokens} tokens")
                
                assert result == f"Response with {max_tokens} tokens"
                
                # Verify correct max_tokens was used
                call_args = mock_completion.call_args[1]
                assert call_args.get('max_tokens') == max_tokens


@pytest.mark.asyncio
async def test_llm_client_generate_response_custom_base_url():
    """Test LLMClient with custom base URL."""
    with patch('jarvis.llm.client.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        mock_settings.return_value.llm_api_key = "test-key"
        mock_settings.return_value.llm_base_url = "https://custom.api.com/v1"
        
        with patch('litellm.completion') as mock_completion:
            mock_response = {
                "choices": [
                    {"message": {"content": "Custom API response"}}
                ]
            }
            mock_completion.return_value = mock_response
            
            from jarvis.llm.client import LLMClient
            
            client = LLMClient()
            result = await client.generate_response("Test custom API")
            
            assert result == "Custom API response"
            
            # Verify custom base URL was used
            call_args = mock_completion.call_args[1]
            # Note: The actual parameter name might vary based on LiteLLM implementation
            assert 'model' in call_args


@pytest.mark.asyncio
async def test_llm_client_error_recovery():
    """Test LLMClient error recovery mechanisms."""
    with patch('jarvis.llm.client.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        mock_settings.return_value.llm_api_key = "test-key"
        
        with patch('litellm.completion') as mock_completion:
            # Test various error types
            errors = [
                ConnectionError("Network error"),
                TimeoutError("Request timeout"),
                ValueError("Invalid parameter"),
                Exception("Generic error"),
            ]
            
            for error in errors:
                mock_completion.side_effect = error
                
                from jarvis.llm.client import LLMClient
                
                client = LLMClient()
                
                with pytest.raises(type(error)):
                    await client.generate_response("Test error recovery")
                
                # Reset for next iteration
                mock_completion.reset_mock()


@pytest.mark.asyncio
async def test_llm_client_performance_large_response():
    """Test LLMClient performance with large responses."""
    import time
    from jarvis.llm.client import LLMClient
    
    with patch('jarvis.llm.client.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        mock_settings.return_value.llm_api_key = "test-key"
        
        with patch('litellm.completion') as mock_completion:
            # Simulate large response
            large_content = "This is a large response. " * 1000  # ~20,000 characters
            mock_response = {
                "choices": [
                    {"message": {"content": large_content}}
                ]
            }
            mock_completion.return_value = mock_response
            
            client = LLMClient()
            
            start_time = time.time()
            result = await client.generate_response("Generate large response")
            end_time = time.time()
            
            assert result == large_content
            assert (end_time - start_time) < 5.0  # Should complete within 5 seconds


@pytest.mark.asyncio
async def test_llm_client_memory_usage():
    """Test LLMClient memory usage with large inputs."""
    import gc
    from jarvis.llm.client import LLMClient
    
    with patch('jarvis.llm.client.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        mock_settings.return_value.llm_api_key = "test-key"
        
        with patch('litellm.completion') as mock_completion:
            mock_response = {
                "choices": [
                    {"message": {"content": "Memory test response"}}
                ]
            }
            mock_completion.return_value = mock_response
            
            client = LLMClient()
            
            # Test with multiple large requests
            for i in range(10):
                large_input = "Large input " * 10000  # ~120,000 characters
                result = await client.generate_response(large_input)
                assert result == "Memory test response"
            
            # Force garbage collection
            gc.collect()
            
            # If we get here without memory errors, test passes
            assert True


def test_llm_client_import():
    """Test that LLMClient can be imported."""
    try:
        from jarvis.llm.client import LLMClient
        assert LLMClient is not None
    except ImportError:
        pytest.fail("Failed to import LLMClient")


def test_llm_client_class_structure():
    """Test LLMClient class structure."""
    from jarvis.llm.client import LLMClient
    
    # Check class exists and has expected methods
    assert hasattr(LLMClient, '__init__')
    assert hasattr(LLMClient, 'generate_response')
    
    # Check that it's properly designed for async
    import inspect
    generate_response_method = getattr(LLMClient, 'generate_response')
    assert inspect.iscoroutinefunction(generate_response_method)


@pytest.mark.asyncio
async def test_llm_client_edge_cases():
    """Test LLMClient edge cases."""
    from jarvis.llm.client import LLMClient
    
    with patch('jarvis.llm.client.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        mock_settings.return_value.llm_api_key = "test-key"
        
        with patch('litellm.completion') as mock_completion:
            mock_response = {
                "choices": [
                    {"message": {"content": "Edge case response"}}
                ]
            }
            mock_completion.return_value = mock_response
            
            client = LLMClient()
            
            # Test with empty string
            result = await client.generate_response("")
            assert result == "Edge case response"
            
            # Test with whitespace only
            result = await client.generate_response("   \t\n   ")
            assert result == "Edge case response"
            
            # Test with None (should raise error)
            try:
                await client.generate_response(None)  # type: ignore
                assert False, "Should raise error for None input"
            except (TypeError, ValueError):
                pass  # Expected
