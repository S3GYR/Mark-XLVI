"""Real tests for Live Session components matching actual implementation."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
from typing import Any


def test_clean_transcript_function():
    """Test the transcript cleaning function."""
    from jarvis.core.live_session import _clean_transcript
    
    # Test normal text
    assert _clean_transcript("Hello world") == "Hello world"
    
    # Test text with control characters
    assert _clean_transcript("Hello<ctrl123>world") == "Helloworld"
    
    # Test text with non-printable characters
    assert _clean_transcript("Hello\x01world") == "Helloworld"
    
    # Test mixed case control tags
    assert _clean_transcript("Hello<CTRL456>world") == "Helloworld"
    
    # Test empty string
    assert _clean_transcript("") == ""
    
    # Test whitespace trimming
    assert _clean_transcript("  Hello world  ") == "Hello world"


def test_load_system_prompt():
    """Test system prompt loading."""
    from jarvis.core.live_session import _load_system_prompt
    
    # Should return a string (either from file or default)
    prompt = _load_system_prompt()
    assert isinstance(prompt, str)
    assert len(prompt) > 0
    assert "JARVIS" in prompt or "AI assistant" in prompt


def test_live_session_initialization():
    """Test live session initialization with proper configuration."""
    with patch('jarvis.core.live_session.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "gemini/gemini-2.5-flash"
        
        with patch('jarvis.core.live_session.get_memory_store') as mock_memory:
            mock_memory.return_value = Mock()
            
            with patch('jarvis.core.live_session.AudioCapture') as mock_capture:
                with patch('jarvis.core.live_session.AudioPlayback') as mock_playback:
                    with patch('jarvis.core.live_session.PhoneAudioRelay') as mock_phone:
                        with patch('jarvis.core.live_session.Player') as mock_player:
                            with patch('jarvis.core.live_session.ToolRunner') as mock_tool_runner:
                                
                                from jarvis.core.live_session import GeminiLiveSession
                                session = GeminiLiveSession()
                                
                                assert session is not None
                                assert session.settings == mock_settings.return_value
                                assert session.memory == mock_memory.return_value
                                assert not session._session


def test_live_session_constants():
    """Test live session constants."""
    from jarvis.core.live_session import (
        LIVE_MODEL, CHANNELS, SEND_SAMPLE_RATE, 
        RECEIVE_SAMPLE_RATE, CHUNK_SIZE
    )
    
    assert LIVE_MODEL == "models/gemini-2.5-flash-native-audio-preview-12-2025"
    assert CHANNELS == 1
    assert SEND_SAMPLE_RATE == 16000
    assert RECEIVE_SAMPLE_RATE == 24000
    assert CHUNK_SIZE == 1024


def test_live_session_audio_relay_integration():
    """Test audio relay integration."""
    with patch('jarvis.core.live_session.get_settings'):
        with patch('jarvis.core.live_session.get_memory_store') as mock_memory:
            mock_memory.return_value = Mock()
            
            with patch('jarvis.core.live_session.AudioCapture'):
                with patch('jarvis.core.live_session.AudioPlayback'):
                    with patch('jarvis.core.live_session.PhoneAudioRelay') as mock_phone:
                        with patch('jarvis.core.live_session.Player'):
                            with patch('jarvis.core.live_session.ToolRunner'):
                                
                                from jarvis.core.live_session import GeminiLiveSession
                                session = GeminiLiveSession()
                                
                                # Test phone relay setup
                                mock_phone.assert_called_once()
                                assert session.phone_relay is not None


def test_live_session_setup():
    """Test live session setup with mocked components."""
    with patch('jarvis.core.live_session.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "gemini/gemini-2.5-flash"
        
        with patch('jarvis.core.live_session.get_memory_store') as mock_memory:
            mock_memory.return_value = Mock()
            
            with patch('jarvis.core.live_session.AudioCapture'):
                with patch('jarvis.core.live_session.AudioPlayback'):
                    with patch('jarvis.core.live_session.PhoneAudioRelay'):
                        with patch('jarvis.core.live_session.Player') as mock_player:
                            with patch('jarvis.core.live_session.ToolRunner') as mock_tool_runner:
                                
                                from jarvis.core.live_session import GeminiLiveSession
                                session = GeminiLiveSession()
                                
                                # Mock setup
                                with patch('google.genai.configure') as mock_configure:
                                    with patch('google.genai.Client') as mock_client:
                                        with patch.object(session, '_load_system_prompt') as mock_prompt:
                                            mock_prompt.return_value = "Test prompt"
                                            
                                            session.setup()
                                            
                                            mock_configure.assert_called_once()
                                            mock_client.assert_called_once()


def test_live_session_start_stop():
    """Test live session start and stop functionality."""
    with patch('jarvis.core.live_session.get_settings'):
        with patch('jarvis.core.live_session.get_memory_store') as mock_memory:
            mock_memory.return_value = Mock()
            
            with patch('jarvis.core.live_session.AudioCapture') as mock_capture:
                with patch('jarvis.core.live_session.AudioPlayback') as mock_playback:
                    with patch('jarvis.core.live_session.PhoneAudioRelay'):
                        with patch('jarvis.core.live_session.Player'):
                            with patch('jarvis.core.live_session.ToolRunner'):
                                
                                from jarvis.core.live_session import GeminiLiveSession
                                session = GeminiLiveSession()
                                
                                # Mock session
                                mock_session = Mock()
                                session._session = mock_session
                                
                                async def test_start_stop():
                                    # Mock start
                                    with patch.object(session, '_start_audio') as mock_start_audio:
                                        with patch.object(session, '_start_tools') as mock_start_tools:
                                            
                                            await session.start()
                                            
                                            mock_start_audio.assert_called_once()
                                            mock_start_tools.assert_called_once()
                                    
                                    # Mock stop
                                    with patch.object(session, '_stop_audio') as mock_stop_audio:
                                        with patch.object(session, '_stop_tools') as mock_stop_tools:
                                            
                                            await session.stop()
                                            
                                            mock_stop_audio.assert_called_once()
                                            mock_stop_tools.assert_called_once()
                                
                                asyncio.run(test_start_stop())


def test_live_session_audio_handling():
    """Test audio data handling."""
    with patch('jarvis.core.live_session.get_settings'):
        with patch('jarvis.core.live_session.get_memory_store') as mock_memory:
            mock_memory.return_value = Mock()
            
            with patch('jarvis.core.live_session.AudioCapture'):
                with patch('jarvis.core.live_session.AudioPlayback'):
                    with patch('jarvis.core.live_session.PhoneAudioRelay'):
                        with patch('jarvis.core.live_session.Player'):
                            with patch('jarvis.core.live_session.ToolRunner'):
                                
                                from jarvis.core.live_session import GeminiLiveSession
                                session = GeminiLiveSession()
                                
                                # Mock session and audio handling
                                mock_session = Mock()
                                session._session = mock_session
                                
                                test_audio = b"test_audio_data"
                                
                                # Test audio input
                                session._on_audio_input(test_audio)
                                
                                # Test phone relay callback
                                mock_phone_data = {"data": test_audio, "mime_type": "audio/pcm"}
                                session._on_phone_audio(mock_phone_data)


def test_live_session_tool_execution():
    """Test tool execution in live session."""
    with patch('jarvis.core.live_session.get_settings'):
        with patch('jarvis.core.live_session.get_memory_store') as mock_memory:
            mock_memory.return_value = Mock()
            
            with patch('jarvis.core.live_session.AudioCapture'):
                with patch('jarvis.core.live_session.AudioPlayback'):
                    with patch('jarvis.core.live_session.PhoneAudioRelay'):
                        with patch('jarvis.core.live_session.Player') as mock_player:
                            mock_player_instance = Mock()
                            
                            with patch('jarvis.core.live_session.ToolRunner') as mock_tool_runner:
                                mock_tool_runner_instance = Mock()
                                mock_tool_runner.return_value = mock_tool_runner_instance
                                
                                from jarvis.core.live_session import GeminiLiveSession
                                session = GeminiLiveSession()
                                
                                # Mock tool execution
                                async def test_tool_execution():
                                    mock_tool_runner_instance.run.return_value = "Tool executed"
                                    
                                    result = await session._execute_tool("test_tool", {"param": "value"})
                                    
                                    assert result == "Tool executed"
                                    mock_tool_runner_instance.run.assert_called_once_with("test_tool", {"param": "value"})
                                
                                asyncio.run(test_tool_execution())


def test_live_session_error_handling():
    """Test error handling in live session."""
    with patch('jarvis.core.live_session.get_settings'):
        with patch('jarvis.core.live_session.get_memory_store') as mock_memory:
            mock_memory.return_value = Mock()
            
            with patch('jarvis.core.live_session.AudioCapture'):
                with patch('jarvis.core.live_session.AudioPlayback'):
                    with patch('jarvis.core.live_session.PhoneAudioRelay'):
                        with patch('jarvis.core.live_session.Player'):
                            with patch('jarvis.core.live_session.ToolRunner'):
                                
                                from jarvis.core.live_session import GeminiLiveSession
                                session = GeminiLiveSession()
                                
                                # Test error logging
                                with patch('jarvis.core.live_session.logger') as mock_logger:
                                    session._log_error("Test error", {"context": "test"})
                                    
                                    mock_logger.error.assert_called_once()


def test_live_session_memory_integration():
    """Test memory store integration."""
    with patch('jarvis.core.live_session.get_settings'):
        with patch('jarvis.core.live_session.get_memory_store') as mock_memory:
            mock_memory_instance = Mock()
            mock_memory.return_value = mock_memory_instance
            
            with patch('jarvis.core.live_session.AudioCapture'):
                with patch('jarvis.core.live_session.AudioPlayback'):
                    with patch('jarvis.core.live_session.PhoneAudioRelay'):
                        with patch('jarvis.core.live_session.Player'):
                            with patch('jarvis.core.live_session.ToolRunner'):
                                
                                from jarvis.core.live_session import GeminiLiveSession
                                session = GeminiLiveSession()
                                
                                # Test memory operations
                                async def test_memory_ops():
                                    mock_memory_instance.add.return_value = "memory_added"
                                    mock_memory_instance.search.return_value = ["result1", "result2"]
                                    
                                    # Add to memory
                                    result = await session._add_to_memory("test content", "test_category")
                                    assert result == "memory_added"
                                    
                                    # Search memory
                                    results = await session._search_memory("test query")
                                    assert results == ["result1", "result2"]
                                
                                asyncio.run(test_memory_ops())


def test_live_session_configuration():
    """Test live session configuration."""
    with patch('jarvis.core.live_session.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "gemini/gemini-2.5-flash"
        
        with patch('jarvis.core.live_session.get_memory_store') as mock_memory:
            mock_memory.return_value = Mock()
            
            with patch('jarvis.core.live_session.AudioCapture'):
                with patch('jarvis.core.live_session.AudioPlayback'):
                    with patch('jarvis.core.live_session.PhoneAudioRelay'):
                        with patch('jarvis.core.live_session.Player'):
                            with patch('jarvis.core.live_session.ToolRunner'):
                                
                                from jarvis.core.live_session import GeminiLiveSession
                                session = GeminiLiveSession()
                                
                                # Test configuration properties
                                from jarvis.core.live_session import LIVE_MODEL, CHANNELS, SEND_SAMPLE_RATE, RECEIVE_SAMPLE_RATE, CHUNK_SIZE
                                assert session.model == LIVE_MODEL
                                assert session.channels == CHANNELS
                                assert session.send_sample_rate == SEND_SAMPLE_RATE
                                assert session.receive_sample_rate == RECEIVE_SAMPLE_RATE
                                assert session.chunk_size == CHUNK_SIZE


def test_live_session_cleanup():
    """Test proper cleanup of live session resources."""
    with patch('jarvis.core.live_session.get_settings'):
        with patch('jarvis.core.live_session.get_memory_store') as mock_memory:
            mock_memory.return_value = Mock()
            
            with patch('jarvis.core.live_session.AudioCapture') as mock_capture:
                with patch('jarvis.core.live_session.AudioPlayback') as mock_playback:
                    with patch('jarvis.core.live_session.PhoneAudioRelay') as mock_phone:
                        with patch('jarvis.core.live_session.Player'):
                            with patch('jarvis.core.live_session.ToolRunner'):
                                
                                from jarvis.core.live_session import GeminiLiveSession
                                session = GeminiLiveSession()
                                
                                # Set up mock components
                                session.capture = Mock()
                                session.playback = Mock()
                                session.phone_relay = Mock()
                                session._session = Mock()
                                
                                async def test_cleanup():
                                    await session.cleanup()
                                    
                                    # Verify cleanup calls
                                    session.capture.stop.assert_called_once()
                                    session.playback.stop.assert_called_once()
                                    session.phone_relay.stop.assert_called_once()
                                
                                asyncio.run(test_cleanup())
