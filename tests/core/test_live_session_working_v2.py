"""Working tests for live session with minimal dependencies."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
from typing import Any


def test_live_session_import():
    """Test that live session imports correctly."""
    try:
        from jarvis.core.live_session import GeminiLiveSession
        assert GeminiLiveSession is not None
    except ImportError:
        pytest.fail("Failed to import GeminiLiveSession")


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
    """Test live session initialization with minimal mocking."""
    with patch('jarvis.core.live_session.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "gemini/gemini-2.5-flash"
        
        # Mock the player
        mock_player = Mock()
        
        with patch('jarvis.core.live_session.ToolRunner') as mock_tool_runner:
            from jarvis.core.live_session import GeminiLiveSession
            session = GeminiLiveSession(player=mock_player)
            
            assert session is not None
            assert session.player == mock_player
            assert session.settings == mock_settings.return_value
            assert session.session is None
            assert session._tool_runner is not None


def test_live_session_api_key():
    """Test API key retrieval."""
    with patch('jarvis.core.live_session.get_secret') as mock_secret:
        mock_secret.return_value = "test_api_key"
        
        mock_player = Mock()
        
        with patch('jarvis.core.live_session.ToolRunner'):
            from jarvis.core.live_session import GeminiLiveSession
            session = GeminiLiveSession(player=mock_player)
            
            api_key = session._get_api_key()
            assert api_key == "test_api_key"
            mock_secret.assert_called_once_with("gemini_api_key", env_override="GEMINI_API_KEY")


def test_live_session_api_key_missing():
    """Test API key missing error."""
    with patch('jarvis.core.live_session.get_secret') as mock_secret:
        mock_secret.return_value = None
        
        mock_player = Mock()
        
        with patch('jarvis.core.live_session.ToolRunner'):
            from jarvis.core.live_session import GeminiLiveSession
            session = GeminiLiveSession(player=mock_player)
            
            with pytest.raises(RuntimeError, match="Gemini API key not configured"):
                session._get_api_key()


def test_live_session_config_building():
    """Test config building."""
    from jarvis.core.live_session import GeminiLiveSession
    
    with patch('jarvis.core.live_session.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "gemini/gemini-2.5-flash"
        
        mock_player = Mock()
        
        with patch('jarvis.core.live_session.ToolRunner'):
            with patch.object(GeminiLiveSession, '_sync_memory_prompt') as mock_memory:
                mock_memory.return_value = "Test memory context"
                
                session = GeminiLiveSession(player=mock_player)
                
                config = session._build_config()
                
                assert config is not None
                mock_memory.assert_called_once()


def test_live_session_sync_memory():
    """Test sync memory prompt."""
    with patch('jarvis.core.live_session.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "gemini/gemini-2.5-flash"
        
        mock_player = Mock()
        
        with patch('jarvis.core.live_session.ToolRunner'):
            from jarvis.core.live_session import GeminiLiveSession
            session = GeminiLiveSession(player=mock_player)
            
            # Test memory prompt (should not crash)
            memory_prompt = session._sync_memory_prompt()
            
            # Should return string or empty string
            assert isinstance(memory_prompt, str)


def test_live_session_speaking_state():
    """Test speaking state management."""
    with patch('jarvis.core.live_session.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "gemini/gemini-2.5-flash"
        
        mock_player = Mock()
        
        with patch('jarvis.core.live_session.ToolRunner'):
            from jarvis.core.live_session import GeminiLiveSession
            session = GeminiLiveSession(player=mock_player)
            
            # Test initial state
            assert not session._is_speaking
            
            # Test speaking state changes
            session._is_speaking = True
            assert session._is_speaking
            
            session._is_speaking = False
            assert not session._is_speaking


def test_live_session_phone_state():
    """Test phone state management."""
    with patch('jarvis.core.live_session.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "gemini/gemini-2.5-flash"
        
        mock_player = Mock()
        
        with patch('jarvis.core.live_session.ToolRunner'):
            from jarvis.core.live_session import GeminiLiveSession
            session = GeminiLiveSession(player=mock_player)
            
            # Test initial state
            assert not session._phone_active
            
            # Test phone state changes
            session._phone_active = True
            assert session._phone_active
            
            session._phone_active = False
            assert not session._phone_active


def test_live_session_audio_components():
    """Test audio component initialization."""
    with patch('jarvis.core.live_session.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "gemini/gemini-2.5-flash"
        
        mock_player = Mock()
        
        with patch('jarvis.core.live_session.ToolRunner'):
            from jarvis.core.live_session import GeminiLiveSession
            session = GeminiLiveSession(player=mock_player)
            
            # Test initial audio components
            assert session._audio_capture is None
            assert session._audio_playback is None
            assert session._phone_relay is None
            
            # Test setting audio components
            mock_capture = Mock()
            session._audio_capture = mock_capture
            assert session._audio_capture == mock_capture
            
            mock_playback = Mock()
            session._audio_playback = mock_playback
            assert session._audio_playback == mock_playback
            
            mock_phone = Mock()
            session._phone_relay = mock_phone
            assert session._phone_relay == mock_phone


def test_live_session_queue_management():
    """Test queue management."""
    with patch('jarvis.core.live_session.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "gemini/gemini-2.5-flash"
        
        mock_player = Mock()
        
        with patch('jarvis.core.live_session.ToolRunner'):
            from jarvis.core.live_session import GeminiLiveSession
            session = GeminiLiveSession(player=mock_player)
            
            # Test initial queues
            assert session.audio_in_queue is None
            assert session.out_queue is None
            
            # Test setting queues
            mock_queue = Mock()
            session.audio_in_queue = mock_queue
            assert session.audio_in_queue == mock_queue
            
            session.out_queue = mock_queue
            assert session.out_queue == mock_queue


def test_live_session_task_management():
    """Test task management."""
    with patch('jarvis.core.live_session.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "gemini/gemini-2.5-flash"
        
        mock_player = Mock()
        
        with patch('jarvis.core.live_session.ToolRunner'):
            from jarvis.core.live_session import GeminiLiveSession
            session = GeminiLiveSession(player=mock_player)
            
            # Test initial tasks
            assert len(session._tasks) == 0
            
            # Test adding tasks
            mock_task = Mock()
            session._tasks.append(mock_task)
            assert len(session._tasks) == 1
            assert session._tasks[0] == mock_task


def test_live_session_event_management():
    """Test event management."""
    with patch('jarvis.core.live_session.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "gemini/gemini-2.5-flash"
        
        mock_player = Mock()
        
        with patch('jarvis.core.live_session.ToolRunner'):
            from jarvis.core.live_session import GeminiLiveSession
            session = GeminiLiveSession(player=mock_player)
            
            # Test initial event
            assert session._turn_done_event is None
            
            # Test setting event
            mock_event = Mock()
            session._turn_done_event = mock_event
            assert session._turn_done_event == mock_event


def test_live_session_loop_management():
    """Test event loop management."""
    with patch('jarvis.core.live_session.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "gemini/gemini-2.5-flash"
        
        mock_player = Mock()
        
        with patch('jarvis.core.live_session.ToolRunner'):
            from jarvis.core.live_session import GeminiLiveSession
            session = GeminiLiveSession(player=mock_player)
            
            # Test initial loop
            assert session._loop is None
            
            # Test setting loop
            mock_loop = Mock()
            session._loop = mock_loop
            assert session._loop == mock_loop


def test_live_session_tool_runner():
    """Test tool runner integration."""
    with patch('jarvis.core.live_session.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "gemini/gemini-2.5-flash"
        
        mock_player = Mock()
        
        with patch('jarvis.core.live_session.ToolRunner') as mock_tool_runner:
            mock_tool_runner_instance = Mock()
            mock_tool_runner.return_value = mock_tool_runner_instance
            
            from jarvis.core.live_session import GeminiLiveSession
            session = GeminiLiveSession(player=mock_player)
            
            assert session._tool_runner == mock_tool_runner_instance
            mock_tool_runner.assert_called_once_with(mock_player)


def test_live_session_speaking_lock():
    """Test speaking lock functionality."""
    with patch('jarvis.core.live_session.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "gemini/gemini-2.5-flash"
        
        mock_player = Mock()
        
        with patch('jarvis.core.live_session.ToolRunner'):
            from jarvis.core.live_session import GeminiLiveSession
            session = GeminiLiveSession(player=mock_player)
            
            # Test speaking lock exists
            assert session._speaking_lock is not None
            assert hasattr(session._speaking_lock, 'acquire')
            assert hasattr(session._speaking_lock, 'release')
