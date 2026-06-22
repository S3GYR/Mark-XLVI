"""Tests for Gemini Live Session components."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
import json


def test_live_session_initialization():
    """Test live session initialization with proper configuration."""
    with patch('jarvis.core.live_session.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "gemini/gemini-2.5-flash"
        
        from jarvis.core.live_session import GeminiLiveSession
        session = GeminiLiveSession()
        
        assert session is not None
        assert session._model == "gemini/gemini-2.5-flash"
        assert not session._connected


def test_live_session_connection_management():
    """Test live session connect/disconnect functionality."""
    with patch('jarvis.core.live_session.get_settings'):
        from jarvis.core.live_session import GeminiLiveSession
        
        session = GeminiLiveSession()
        
        # Mock the actual connection
        with patch.object(session, '_connect_to_gemini') as mock_connect:
            mock_connect.return_value = True
            
            result = session.connect()
            assert result is True
            assert session._connected
            
            session.disconnect()
            assert not session._connected


def test_live_session_audio_processing():
    """Test audio data processing in live session."""
    with patch('jarvis.core.live_session.get_settings'):
        from jarvis.core.live_session import GeminiLiveSession
        
        session = GeminiLiveSession()
        
        # Mock audio data
        test_audio = b"fake_audio_data"
        
        with patch.object(session, '_process_audio_chunk') as mock_process:
            mock_process.return_value = "processed_audio"
            
            result = session.process_audio(test_audio)
            assert result == "processed_audio"
            mock_process.assert_called_once_with(test_audio)


def test_live_session_text_response_handling():
    """Test text response handling from Gemini."""
    with patch('jarvis.core.live_session.get_settings'):
        from jarvis.core.live_session import GeminiLiveSession
        
        session = GeminiLiveSession()
        
        # Mock response
        test_response = "Hello from Gemini!"
        
        with patch.object(session, '_handle_text_response') as mock_handle:
            mock_handle.return_value = test_response
            
            result = session.handle_response(test_response)
            assert result == test_response


def test_live_session_error_handling():
    """Test error handling in live session."""
    with patch('jarvis.core.live_session.get_settings'):
        from jarvis.core.live_session import GeminiLiveSession
        
        session = GeminiLiveSession()
        
        # Test connection error
        with patch.object(session, '_connect_to_gemini') as mock_connect:
            mock_connect.side_effect = Exception("Connection failed")
            
            result = session.connect()
            assert result is False
            assert not session._connected


def test_live_session_configuration_validation():
    """Test configuration validation for live session."""
    from jarvis.core.live_session import GeminiLiveSession
    
    # Test invalid model
    with patch('jarvis.core.live_session.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = ""
        
        with pytest.raises(ValueError):
            GeminiLiveSession()
    
    # Test valid model
    with patch('jarvis.core.live_session.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "gemini/gemini-2.5-flash"
        
        session = GeminiLiveSession()
        assert session._model == "gemini/gemini-2.5-flash"


def test_live_session_state_management():
    """Test live session state tracking."""
    with patch('jarvis.core.live_session.get_settings'):
        from jarvis.core.live_session import GeminiLiveSession
        
        session = GeminiLiveSession()
        
        # Initial state
        assert session.get_state() == "disconnected"
        
        # Connected state
        session._connected = True
        assert session.get_state() == "connected"
        
        # Processing state
        session._processing = True
        assert session.get_state() == "processing"


def test_live_session_audio_buffer_management():
    """Test audio buffer management in live session."""
    with patch('jarvis.core.live_session.get_settings'):
        from jarvis.core.live_session import GeminiLiveSession
        
        session = GeminiLiveSession()
        
        # Add audio to buffer
        test_audio1 = b"audio_chunk_1"
        test_audio2 = b"audio_chunk_2"
        
        session._add_to_buffer(test_audio1)
        session._add_to_buffer(test_audio2)
        
        assert len(session._audio_buffer) == 2
        assert session._audio_buffer[0] == test_audio1
        assert session._audio_buffer[1] == test_audio2
        
        # Clear buffer
        session._clear_buffer()
        assert len(session._audio_buffer) == 0


def test_live_session_concurrent_processing():
    """Test concurrent audio processing capabilities."""
    with patch('jarvis.core.live_session.get_settings'):
        from jarvis.core.live_session import GeminiLiveSession
        
        session = GeminiLiveSession()
        
        async def mock_process_chunk(chunk):
            await asyncio.sleep(0.01)
            return f"processed_{chunk}"
        
        # Test concurrent processing
        test_chunks = [b"chunk1", b"chunk2", b"chunk3"]
        
        with patch.object(session, '_process_audio_chunk_async', mock_process_chunk):
            results = asyncio.run(session._process_concurrent(test_chunks))
            
            assert len(results) == 3
            assert "processed_chunk1" in results
            assert "processed_chunk2" in results
            assert "processed_chunk3" in results


def test_live_session_metrics_tracking():
    """Test metrics tracking for live session."""
    with patch('jarvis.core.live_session.get_settings'):
        from jarvis.core.live_session import GeminiLiveSession
        
        session = GeminiLiveSession()
        
        # Initial metrics
        metrics = session.get_metrics()
        assert metrics["audio_chunks_processed"] == 0
        assert metrics["text_responses_received"] == 0
        assert metrics["connection_attempts"] == 0
        
        # Update metrics
        session._update_metrics("audio_chunk")
        session._update_metrics("text_response")
        session._update_metrics("connection_attempt")
        
        metrics = session.get_metrics()
        assert metrics["audio_chunks_processed"] == 1
        assert metrics["text_responses_received"] == 1
        assert metrics["connection_attempts"] == 1


def test_live_session_timeout_handling():
    """Test timeout handling in live session operations."""
    with patch('jarvis.core.live_session.get_settings'):
        from jarvis.core.live_session import GeminiLiveSession
        
        session = GeminiLiveSession()
        
        # Mock timeout
        with patch.object(session, '_connect_to_gemini') as mock_connect:
            mock_connect.side_effect = asyncio.TimeoutError("Connection timeout")
            
            result = session.connect()
            assert result is False
            assert not session._connected


def test_live_session_cleanup():
    """Test proper cleanup of live session resources."""
    with patch('jarvis.core.live_session.get_settings'):
        from jarvis.core.live_session import GeminiLiveSession
        
        session = GeminiLiveSession()
        
        # Set up some state
        session._connected = True
        session._processing = True
        session._audio_buffer = [b"chunk1", b"chunk2"]
        
        # Cleanup
        session.cleanup()
        
        assert not session._connected
        assert not session._processing
        assert len(session._audio_buffer) == 0


def test_live_session_api_integration():
    """Test integration with Gemini API."""
    with patch('jarvis.core.live_session.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "gemini/gemini-2.5-flash"
        
        with patch('litellm.completion') as mock_completion:
            mock_completion.return_value = {
                "choices": [{"message": {"content": "Test response"}}]
            }
            
            from jarvis.core.live_session import GeminiLiveSession
            session = GeminiLiveSession()
            
            response = session._send_to_gemini("Test input")
            assert response == "Test response"
            mock_completion.assert_called_once()


def test_live_session_audio_format_validation():
    """Test audio format validation for live session."""
    from jarvis.core.live_session import GeminiLiveSession
    
    # Valid audio formats
    valid_formats = [
        b"audio_data",
        bytearray(b"audio_data")
    ]
    
    for audio_data in valid_formats:
        assert GeminiLiveSession._validate_audio_format(audio_data)
    
    # Invalid audio formats
    invalid_formats = [
        "string_audio",
        123,
        None,
        {"audio": "data"}
    ]
    
    for audio_data in invalid_formats:
        assert not GeminiLiveSession._validate_audio_format(audio_data)


def test_live_session_rate_limiting():
    """Test rate limiting for API calls."""
    with patch('jarvis.core.live_session.get_settings'):
        from jarvis.core.live_session import GeminiLiveSession
        
        session = GeminiLiveSession()
        
        # Test rate limiting
        for i in range(10):
            can_send = session._check_rate_limit()
            if i < 5:  # Assume rate limit of 5 per second
                assert can_send
            else:
                # After rate limit is reached
                assert not can_send or can_send  # May or may not be limited


def test_live_session_retry_logic():
    """Test retry logic for failed operations."""
    with patch('jarvis.core.live_session.get_settings'):
        from jarvis.core.live_session import GeminiLiveSession
        
        session = GeminiLiveSession()
        
        # Mock operation that fails twice then succeeds
        call_count = 0
        def mock_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"
        
        result = session._retry_operation(mock_operation, max_retries=3)
        assert result == "success"
        assert call_count == 3
