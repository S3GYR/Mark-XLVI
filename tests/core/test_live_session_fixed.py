"""Fixed tests for Live Session components."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
from typing import Any


def test_live_session_initialization():
    """Test live session initialization with proper configuration."""
    with patch('jarvis.core.live_session.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "gemini/gemini-2.5-flash"
        
        with patch('jarvis.core.live_session.get_memory_store') as mock_memory:
            mock_memory.return_value = Mock()
            
            from jarvis.core.live_session import GeminiLiveSession
            session = GeminiLiveSession()
            
            assert session is not None
            assert session.settings == mock_settings.return_value
            assert session.memory == mock_memory.return_value
            assert not session._connected


def test_live_session_connection_management():
    """Test live session connect/disconnect functionality."""
    with patch('jarvis.core.live_session.get_settings'):
        with patch('jarvis.core.live_session.get_memory_store') as mock_memory:
            mock_memory.return_value = Mock()
            
            from jarvis.core.live_session import GeminiLiveSession
            session = GeminiLiveSession()
            
            # Mock connection
            with patch.object(session, '_connect_to_gemini') as mock_connect:
                mock_connect.return_value = True
                
                result = session.connect()
                assert result is True
                assert session._connected
                
                session.disconnect()
                assert not session._connected


def test_live_session_audio_processing():
    """Test audio processing functionality."""
    with patch('jarvis.core.live_session.get_settings'):
        with patch('jarvis.core.live_session.get_memory_store') as mock_memory:
            mock_memory.return_value = Mock()
            
            from jarvis.core.live_session import GeminiLiveSession
            session = GeminiLiveSession()
            
            # Mock audio data
            test_audio = b"test_audio_data"
            
            with patch.object(session, '_process_audio') as mock_process:
                mock_process.return_value = "audio_processed"
                
                result = session.process_audio(test_audio)
                assert result == "audio_processed"
                mock_process.assert_called_once_with(test_audio)


def test_live_session_text_response_handling():
    """Test text response handling."""
    with patch('jarvis.core.live_session.get_settings'):
        with patch('jarvis.core.live_session.get_memory_store') as mock_memory:
            mock_memory.return_value = Mock()
            
            from jarvis.core.live_session import GeminiLiveSession
            session = GeminiLiveSession()
            
            # Mock text response
            test_response = "Hello, this is a response"
            
            with patch.object(session, '_handle_text_response') as mock_handle:
                mock_handle.return_value = "response_handled"
                
                result = session.handle_text_response(test_response)
                assert result == "response_handled"
                mock_handle.assert_called_once_with(test_response)


def test_live_session_error_handling():
    """Test error handling in live session operations."""
    with patch('jarvis.core.live_session.get_settings'):
        with patch('jarvis.core.live_session.get_memory_store') as mock_memory:
            mock_memory.return_value = Mock()
            
            from jarvis.core.live_session import GeminiLiveSession
            session = GeminiLiveSession()
            
            # Test connection error
            with patch.object(session, '_connect_to_gemini') as mock_connect:
                mock_connect.side_effect = Exception("Connection failed")
                
                result = session.connect()
                assert result is False
                assert not session._connected


def test_live_session_configuration_validation():
    """Test configuration validation."""
    from jarvis.core.live_session import GeminiLiveSession
    
    # Test valid configuration
    valid_config = {
        "model": "gemini/gemini-2.5-flash",
        "api_key": "test_key",
        "sample_rate": 16000
    }
    
    assert GeminiLiveSession._validate_config(valid_config)
    
    # Test invalid configuration
    invalid_config = {
        "model": "",  # Empty model
        "api_key": None  # Missing API key
    }
    
    assert not GeminiLiveSession._validate_config(invalid_config)


def test_live_session_state_management():
    """Test live session state tracking."""
    with patch('jarvis.core.live_session.get_settings'):
        with patch('jarvis.core.live_session.get_memory_store') as mock_memory:
            mock_memory.return_value = Mock()
            
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
    """Test audio buffer management."""
    with patch('jarvis.core.live_session.get_settings'):
        with patch('jarvis.core.live_session.get_memory_store') as mock_memory:
            mock_memory.return_value = Mock()
            
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
    """Test concurrent audio processing."""
    with patch('jarvis.core.live_session.get_settings'):
        with patch('jarvis.core.live_session.get_memory_store') as mock_memory:
            mock_memory.return_value = Mock()
            
            from jarvis.core.live_session import GeminiLiveSession
            session = GeminiLiveSession()
            
            async def mock_process_chunk(chunk):
                await asyncio.sleep(0.01)
                return f"processed_{chunk}"
            
            # Test concurrent processing
            test_chunks = [b"chunk1", b"chunk2", b"chunk3"]
            
            with patch.object(session, '_process_concurrent', mock_process_chunk):
                results = asyncio.run(session._process_concurrent(test_chunks))
                
                assert len(results) == 3
                assert "processed_chunk1" in results
                assert "processed_chunk2" in results
                assert "processed_chunk3" in results


def test_live_session_metrics_tracking():
    """Test metrics tracking for live session."""
    with patch('jarvis.core.live_session.get_settings'):
        with patch('jarvis.core.live_session.get_memory_store') as mock_memory:
            mock_memory.return_value = Mock()
            
            from jarvis.core.live_session import GeminiLiveSession
            session = GeminiLiveSession()
            
            # Initial metrics
            metrics = session.get_metrics()
            assert metrics["audio_chunks_processed"] == 0
            assert metrics["text_responses_generated"] == 0
            assert metrics["total_processing_time"] == 0
            
            # Update metrics
            session._update_metrics("audio_processed", 1)
            session._update_metrics("text_generated", 1)
            
            metrics = session.get_metrics()
            assert metrics["audio_chunks_processed"] == 1
            assert metrics["text_responses_generated"] == 1


def test_live_session_timeout_handling():
    """Test timeout handling for operations."""
    with patch('jarvis.core.live_session.get_settings'):
        with patch('jarvis.core.live_session.get_memory_store') as mock_memory:
            mock_memory.return_value = Mock()
            
            from jarvis.core.live_session import GeminiLiveSession
            session = GeminiLiveSession()
            
            async def test_timeout():
                with patch.object(session, '_process_with_timeout') as mock_process:
                    mock_process.side_effect = asyncio.TimeoutError()
                    
                    result = await session._process_with_timeout("test_data", timeout=0.1)
                    assert result is None
            
            asyncio.run(test_timeout())


def test_live_session_cleanup():
    """Test proper cleanup of live session resources."""
    with patch('jarvis.core.live_session.get_settings'):
        with patch('jarvis.core.live_session.get_memory_store') as mock_memory:
            mock_memory.return_value = Mock()
            
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
    """Test Gemini API integration."""
    with patch('jarvis.core.live_session.get_settings'):
        with patch('jarvis.core.live_session.get_memory_store') as mock_memory:
            mock_memory.return_value = Mock()
            
            from jarvis.core.live_session import GeminiLiveSession
            session = GeminiLiveSession()
            
            # Mock API call
            with patch('google.generativeai.GenerativeModel') as mock_model:
                mock_model_instance = Mock()
                mock_model.return_value = mock_model_instance
                
                session._setup_api_client()
                
                mock_model.assert_called_once()


def test_live_session_audio_format_validation():
    """Test audio format validation."""
    from jarvis.core.live_session import GeminiLiveSession
    
    # Test valid audio formats
    valid_formats = [
        b"audio_data",
        bytearray(b"audio_data")
    ]
    
    for audio_data in valid_formats:
        assert GeminiLiveSession._validate_audio_format(audio_data)
    
    # Test invalid audio formats
    invalid_formats = [
        "string_audio",
        123,
        None,
        {"audio": "data"}
    ]
    
    for audio_data in invalid_formats:
        assert not GeminiLiveSession._validate_audio_format(audio_data)


def test_live_session_rate_limiting():
    """Test rate limiting functionality."""
    with patch('jarvis.core.live_session.get_settings'):
        with patch('jarvis.core.live_session.get_memory_store') as mock_memory:
            mock_memory.return_value = Mock()
            
            from jarvis.core.live_session import GeminiLiveSession
            session = GeminiLiveSession()
            
            # Test rate limiting
            assert session._check_rate_limit()
            
            # Simulate hitting rate limit
            session._request_count = 100
            session._last_request_time = 0
            
            # Should be rate limited
            assert not session._check_rate_limit()


def test_live_session_retry_logic():
    """Test retry logic for failed operations."""
    with patch('jarvis.core.live_session.get_settings'):
        with patch('jarvis.core.live_session.get_memory_store') as mock_memory:
            mock_memory.return_value = Mock()
            
            from jarvis.core.live_session import GeminiLiveSession
            session = GeminiLiveSession()
            
            async def test_retry():
                call_count = 0
                
                async def failing_operation():
                    nonlocal call_count
                    call_count += 1
                    if call_count < 3:
                        raise Exception("Temporary failure")
                    return "success"
                
                result = await session._retry_operation(failing_operation, max_retries=3)
                assert result == "success"
                assert call_count == 3
            
            asyncio.run(test_retry())
