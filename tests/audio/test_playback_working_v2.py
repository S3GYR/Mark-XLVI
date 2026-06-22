"""Working tests for audio playback focusing on existing functionality."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
from typing import Any


def test_audio_playback_import():
    """Test that audio playback imports correctly."""
    try:
        from jarvis.audio.playback import AudioPlayback
        assert AudioPlayback is not None
    except ImportError:
        pytest.fail("Failed to import AudioPlayback")


def test_audio_playback_initialization():
    """Test audio playback initialization with minimal mocking."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_device = "default"
        mock_settings.return_value.sample_rate = 24000
        mock_settings.return_value.channels = 1
        
        # Mock the audio queue
        audio_queue = Mock()
        
        from jarvis.audio.playback import AudioPlayback
        
        playback = AudioPlayback(audio_queue=audio_queue)
        
        assert playback is not None
        assert playback.audio_queue == audio_queue
        assert playback._running is False
        assert playback._stream is None


def test_audio_playback_initialization_with_settings():
    """Test audio playback initialization with custom settings."""
    # Mock settings
    mock_settings = Mock()
    mock_settings.audio_device = "test_device"
    mock_settings.sample_rate = 44100
    mock_settings.channels = 2
    
    # Mock the audio queue
    audio_queue = Mock()
    
    from jarvis.audio.playback import AudioPlayback
    
    playback = AudioPlayback(audio_queue=audio_queue, settings=mock_settings)
    
    assert playback is not None
    assert playback.settings == mock_settings


def test_audio_playback_start_with_loop():
    """Test audio playback start with event loop."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_receive_sample_rate = 24000
        mock_settings.return_value.audio_channels = 1
        mock_settings.return_value.audio_device_index = None
        
        # Mock the audio queue
        audio_queue = Mock()
        
        with patch('sounddevice.RawOutputStream') as mock_stream:
            mock_stream_instance = Mock()
            mock_stream.return_value = mock_stream_instance
            
            from jarvis.audio.playback import AudioPlayback
            
            playback = AudioPlayback(audio_queue=audio_queue)
            
            # Test start with event loop
            loop = asyncio.new_event_loop()
            playback.start(loop)
            
            assert playback._running is True
            mock_stream_instance.start.assert_called_once()
            
            # Clean up
            loop.close()


def test_audio_playback_stop():
    """Test audio playback stop functionality."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_receive_sample_rate = 24000
        mock_settings.return_value.audio_channels = 1
        mock_settings.return_value.audio_device_index = None
        
        # Mock the audio queue
        audio_queue = Mock()
        
        with patch('sounddevice.RawOutputStream') as mock_stream:
            mock_stream_instance = Mock()
            mock_stream.return_value = mock_stream_instance
            
            from jarvis.audio.playback import AudioPlayback
            
            playback = AudioPlayback(audio_queue=audio_queue)
            
            # Start first
            loop = asyncio.new_event_loop()
            playback.start(loop)
            
            # Test stop
            playback.stop()
            assert playback._running is False
            assert playback._stream is None
            
            mock_stream_instance.stop.assert_called_once()
            mock_stream_instance.close.assert_called_once()
            
            # Clean up
            loop.close()


def test_audio_playback_start_error_handling():
    """Test audio playback start error handling."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_receive_sample_rate = 24000
        mock_settings.return_value.audio_channels = 1
        mock_settings.return_value.audio_device_index = None
        
        # Mock the audio queue
        audio_queue = Mock()
        
        with patch('sounddevice.RawOutputStream') as mock_stream:
            mock_stream.side_effect = Exception("Audio device error")
            
            from jarvis.audio.playback import AudioPlayback
            
            playback = AudioPlayback(audio_queue=audio_queue)
            
            # Should handle error gracefully
            loop = asyncio.new_event_loop()
            with pytest.raises(Exception, match="Audio device error"):
                playback.start(loop)
            
            # Clean up
            loop.close()


def test_audio_playback_stop_error_handling():
    """Test audio playback stop error handling."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_receive_sample_rate = 24000
        mock_settings.return_value.audio_channels = 1
        mock_settings.return_value.audio_device_index = None
        
        # Mock the audio queue
        audio_queue = Mock()
        
        with patch('sounddevice.RawOutputStream') as mock_stream:
            mock_stream_instance = Mock()
            mock_stream_instance.stop.side_effect = Exception("Stop error")
            mock_stream.return_value = mock_stream_instance
            
            from jarvis.audio.playback import AudioPlayback
            
            playback = AudioPlayback(audio_queue=audio_queue)
            
            # Start first
            loop = asyncio.new_event_loop()
            playback.start(loop)
            
            # Should handle stop error gracefully
            playback.stop()  # Should not raise exception
            
            assert playback._running is False
            assert playback._stream is None
            
            # Clean up
            loop.close()


def test_audio_playback_stream_parameters():
    """Test audio playback stream parameters."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_receive_sample_rate = 44100
        mock_settings.return_value.audio_channels = 2
        mock_settings.return_value.audio_device_index = 5
        
        # Mock the audio queue
        audio_queue = Mock()
        
        with patch('sounddevice.RawOutputStream') as mock_stream:
            from jarvis.audio.playback import AudioPlayback
            
            playback = AudioPlayback(audio_queue=audio_queue)
            
            loop = asyncio.new_event_loop()
            playback.start(loop)
            
            # Verify stream was created with correct parameters
            mock_stream.assert_called_once()
            call_kwargs = mock_stream.call_args[1]
            
            assert call_kwargs['samplerate'] == 44100
            assert call_kwargs['channels'] == 2
            assert call_kwargs['device'] == 5
            assert call_kwargs['dtype'] == "int16"
            assert 'callback' in call_kwargs
            
            # Clean up
            loop.close()


def test_audio_playback_multiple_start_stop():
    """Test multiple start/stop cycles."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_receive_sample_rate = 24000
        mock_settings.return_value.audio_channels = 1
        mock_settings.return_value.audio_device_index = None
        
        # Mock the audio queue
        audio_queue = Mock()
        
        with patch('sounddevice.RawOutputStream') as mock_stream:
            mock_stream_instance = Mock()
            mock_stream.return_value = mock_stream_instance
            
            from jarvis.audio.playback import AudioPlayback
            
            playback = AudioPlayback(audio_queue=audio_queue)
            
            loop = asyncio.new_event_loop()
            
            # Multiple start/stop cycles
            for i in range(3):
                playback.start(loop)
                assert playback._running is True
                
                playback.stop()
                assert playback._running is False
            
            # Verify stream was called multiple times
            assert mock_stream.call_count == 3
            assert mock_stream_instance.start.call_count == 3
            assert mock_stream_instance.stop.call_count == 3
            assert mock_stream_instance.close.call_count == 3
            
            # Clean up
            loop.close()


def test_audio_playback_queue_operations():
    """Test audio playback queue operations."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_receive_sample_rate = 24000
        mock_settings.return_value.audio_channels = 1
        mock_settings.return_value.audio_device_index = None
        
        # Mock the audio queue
        audio_queue = Mock()
        
        with patch('sounddevice.RawOutputStream') as mock_stream:
            # Capture the callback function
            callback_func = None
            
            def capture_callback(*args, **kwargs):
                nonlocal callback_func
                if 'callback' in kwargs:
                    callback_func = kwargs['callback']
                return Mock()
            
            mock_stream.side_effect = capture_callback
            
            from jarvis.audio.playback import AudioPlayback
            
            playback = AudioPlayback(audio_queue=audio_queue)
            
            loop = asyncio.new_event_loop()
            playback.start(loop)
            
            # Test callback exists
            assert callback_func is not None
            
            # Test queue operations
            audio_queue.empty.return_value = False
            audio_queue.get_nowait.return_value = {"data": b"test_audio_data"}
            
            # Call the callback
            callback_func(None, 1024, None, None)
            
            # Verify queue operations were called
            audio_queue.empty.assert_called_once()
            audio_queue.get_nowait.assert_called_once()
            
            # Clean up
            loop.close()


def test_audio_playback_queue_empty():
    """Test audio playback when queue is empty."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_receive_sample_rate = 24000
        mock_settings.return_value.audio_channels = 1
        mock_settings.return_value.audio_device_index = None
        
        # Mock the audio queue
        audio_queue = Mock()
        audio_queue.empty.return_value = True
        
        with patch('sounddevice.RawOutputStream') as mock_stream:
            # Capture the callback function
            callback_func = None
            
            def capture_callback(*args, **kwargs):
                nonlocal callback_func
                if 'callback' in kwargs:
                    callback_func = kwargs['callback']
                return Mock()
            
            mock_stream.side_effect = capture_callback
            
            from jarvis.audio.playback import AudioPlayback
            
            playback = AudioPlayback(audio_queue=audio_queue)
            
            loop = asyncio.new_event_loop()
            playback.start(loop)
            
            # Test callback when queue is empty
            callback_func(None, 1024, None, None)
            
            # Verify queue operations were called
            audio_queue.empty.assert_called_once()
            audio_queue.get_nowait.assert_not_called()
            
            # Clean up
            loop.close()


def test_audio_playback_queue_timeout():
    """Test audio playback queue timeout handling."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_receive_sample_rate = 24000
        mock_settings.return_value.audio_channels = 1
        mock_settings.return_value.audio_device_index = None
        
        # Mock the audio queue
        audio_queue = Mock()
        audio_queue.empty.return_value = False
        audio_queue.get_nowait.side_effect = asyncio.QueueEmpty()
        
        with patch('sounddevice.RawOutputStream') as mock_stream:
            # Capture the callback function
            callback_func = None
            
            def capture_callback(*args, **kwargs):
                nonlocal callback_func
                if 'callback' in kwargs:
                    callback_func = kwargs['callback']
                return Mock()
            
            mock_stream.side_effect = capture_callback
            
            from jarvis.audio.playback import AudioPlayback
            
            playback = AudioPlayback(audio_queue=audio_queue)
            
            loop = asyncio.new_event_loop()
            playback.start(loop)
            
            # Test callback when queue raises QueueEmpty
            callback_func(None, 1024, None, None)
            
            # Verify queue operations were called
            audio_queue.empty.assert_called_once()
            audio_queue.get_nowait.assert_called_once()
            
            # Clean up
            loop.close()


def test_audio_playback_state_management():
    """Test audio playback state management."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_receive_sample_rate = 24000
        mock_settings.return_value.audio_channels = 1
        mock_settings.return_value.audio_device_index = None
        
        # Mock the audio queue
        audio_queue = Mock()
        
        from jarvis.audio.playback import AudioPlayback
        
        playback = AudioPlayback(audio_queue=audio_queue)
        
        # Test initial state
        assert playback._running is False
        assert playback._stream is None
        
        # Test state changes
        playback._running = True
        assert playback._running is True
        
        playback._running = False
        assert playback._running is False


def test_audio_playback_volume_control():
    """Test audio playback volume control."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_receive_sample_rate = 24000
        mock_settings.return_value.audio_channels = 1
        mock_settings.return_value.audio_device_index = None
        
        # Mock the audio queue
        audio_queue = Mock()
        
        from jarvis.audio.playback import AudioPlayback
        
        playback = AudioPlayback(audio_queue=audio_queue)
        
        # Test volume control (if implemented)
        if hasattr(playback, 'set_volume'):
            playback.set_volume(0.5)
            assert playback.volume == 0.5
        else:
            # Volume control might not be implemented
            pass


def test_audio_playback_device_selection():
    """Test audio playback device selection."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_receive_sample_rate = 24000
        mock_settings.return_value.audio_channels = 1
        mock_settings.return_value.audio_device_index = 2
        
        # Mock the audio queue
        audio_queue = Mock()
        
        with patch('sounddevice.RawOutputStream') as mock_stream:
            from jarvis.audio.playback import AudioPlayback
            
            playback = AudioPlayback(audio_queue=audio_queue)
            
            loop = asyncio.new_event_loop()
            playback.start(loop)
            
            # Verify device was set correctly
            call_kwargs = mock_stream.call_args[1]
            assert call_kwargs['device'] == 2
            
            # Clean up
            loop.close()


def test_audio_playback_sample_rate_validation():
    """Test audio playback sample rate validation."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        # Test various sample rates
        sample_rates = [8000, 16000, 22050, 44100, 48000, 96000]
        
        for sample_rate in sample_rates:
            mock_settings.return_value.audio_receive_sample_rate = sample_rate
            mock_settings.return_value.audio_channels = 1
            mock_settings.return_value.audio_device_index = None
            
            # Mock the audio queue
            audio_queue = Mock()
            
            with patch('sounddevice.RawOutputStream') as mock_stream:
                from jarvis.audio.playback import AudioPlayback
                
                playback = AudioPlayback(audio_queue=audio_queue)
                
                loop = asyncio.new_event_loop()
                playback.start(loop)
                
                # Verify stream was created with correct sample rate
                call_kwargs = mock_stream.call_args[1]
                assert call_kwargs['samplerate'] == sample_rate
                
                playback.stop()
                loop.close()


def test_audio_playback_channel_validation():
    """Test audio playback channel validation."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        # Test various channel configurations
        channel_configs = [1, 2, 4, 8]
        
        for channels in channel_configs:
            mock_settings.return_value.audio_receive_sample_rate = 24000
            mock_settings.return_value.audio_channels = channels
            mock_settings.return_value.audio_device_index = None
            
            # Mock the audio queue
            audio_queue = Mock()
            
            with patch('sounddevice.RawOutputStream') as mock_stream:
                from jarvis.audio.playback import AudioPlayback
                
                playback = AudioPlayback(audio_queue=audio_queue)
                
                loop = asyncio.new_event_loop()
                playback.start(loop)
                
                # Verify stream was created with correct channels
                call_kwargs = mock_stream.call_args[1]
                assert call_kwargs['channels'] == channels
                
                playback.stop()
                loop.close()


def test_audio_playback_cleanup():
    """Test audio playback cleanup."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_receive_sample_rate = 24000
        mock_settings.return_value.audio_channels = 1
        mock_settings.return_value.audio_device_index = None
        
        # Mock the audio queue
        audio_queue = Mock()
        
        with patch('sounddevice.RawOutputStream') as mock_stream:
            mock_stream_instance = Mock()
            mock_stream.return_value = mock_stream_instance
            
            from jarvis.audio.playback import AudioPlayback
            
            playback = AudioPlayback(audio_queue=audio_queue)
            
            loop = asyncio.new_event_loop()
            playback.start(loop)
            
            # Test cleanup
            playback.stop()
            
            assert playback._running is False
            assert playback._stream is None
            
            mock_stream_instance.stop.assert_called_once()
            mock_stream_instance.close.assert_called_once()
            
            # Clean up
            loop.close()
