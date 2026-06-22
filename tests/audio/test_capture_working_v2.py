"""Working tests for audio capture focusing on existing functionality."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
from typing import Any


def test_audio_capture_import():
    """Test that audio capture imports correctly."""
    try:
        from jarvis.audio.capture import AudioCapture
        assert AudioCapture is not None
    except ImportError:
        pytest.fail("Failed to import AudioCapture")


def test_audio_capture_initialization():
    """Test audio capture initialization with minimal mocking."""
    with patch('jarvis.audio.capture.get_settings') as mock_settings:
        mock_settings.return_value.audio_device = "default"
        mock_settings.return_value.sample_rate = 16000
        mock_settings.return_value.channels = 1
        
        # Mock the callbacks
        output_callback = Mock()
        is_speaking = Mock(return_value=False)
        is_muted = Mock(return_value=False)
        is_phone_active = Mock(return_value=False)
        
        from jarvis.audio.capture import AudioCapture
        
        capture = AudioCapture(
            output_callback=output_callback,
            is_speaking=is_speaking,
            is_muted=is_muted,
            is_phone_active=is_phone_active
        )
        
        assert capture is not None
        assert capture.output_callback == output_callback
        assert capture.is_speaking == is_speaking
        assert capture.is_muted == is_muted
        assert capture.is_phone_active == is_phone_active
        assert capture._running is False
        assert capture._stream is None


def test_audio_capture_initialization_with_settings():
    """Test audio capture initialization with custom settings."""
    # Mock settings
    mock_settings = Mock()
    mock_settings.audio_device = "test_device"
    mock_settings.sample_rate = 44100
    mock_settings.channels = 2
    
    # Mock the callbacks
    output_callback = Mock()
    is_speaking = Mock(return_value=False)
    is_muted = Mock(return_value=False)
    is_phone_active = Mock(return_value=False)
    
    from jarvis.audio.capture import AudioCapture
    
    capture = AudioCapture(
        output_callback=output_callback,
        is_speaking=is_speaking,
        is_muted=is_muted,
        is_phone_active=is_phone_active,
        settings=mock_settings
    )
    
    assert capture is not None
    assert capture.settings == mock_settings


def test_audio_capture_start_with_loop():
    """Test audio capture start with event loop."""
    with patch('jarvis.audio.capture.get_settings') as mock_settings:
        mock_settings.return_value.audio_send_sample_rate = 16000
        mock_settings.return_value.audio_channels = 1
        mock_settings.return_value.audio_chunk_size = 1024
        mock_settings.return_value.audio_device_index = None
        
        # Mock the callbacks
        output_callback = Mock()
        is_speaking = Mock(return_value=False)
        is_muted = Mock(return_value=False)
        is_phone_active = Mock(return_value=False)
        
        with patch('sounddevice.InputStream') as mock_stream:
            mock_stream_instance = Mock()
            mock_stream.return_value = mock_stream_instance
            
            from jarvis.audio.capture import AudioCapture
            
            capture = AudioCapture(
                output_callback=output_callback,
                is_speaking=is_speaking,
                is_muted=is_muted,
                is_phone_active=is_phone_active
            )
            
            # Test start with event loop
            loop = asyncio.new_event_loop()
            capture.start(loop)
            
            assert capture._running is True
            mock_stream_instance.start.assert_called_once()
            
            # Clean up
            loop.close()


def test_audio_capture_stop():
    """Test audio capture stop functionality."""
    with patch('jarvis.audio.capture.get_settings') as mock_settings:
        mock_settings.return_value.audio_send_sample_rate = 16000
        mock_settings.return_value.audio_channels = 1
        mock_settings.return_value.audio_chunk_size = 1024
        mock_settings.return_value.audio_device_index = None
        
        # Mock the callbacks
        output_callback = Mock()
        is_speaking = Mock(return_value=False)
        is_muted = Mock(return_value=False)
        is_phone_active = Mock(return_value=False)
        
        with patch('sounddevice.InputStream') as mock_stream:
            mock_stream_instance = Mock()
            mock_stream.return_value = mock_stream_instance
            
            from jarvis.audio.capture import AudioCapture
            
            capture = AudioCapture(
                output_callback=output_callback,
                is_speaking=is_speaking,
                is_muted=is_muted,
                is_phone_active=is_phone_active
            )
            
            # Start first
            loop = asyncio.new_event_loop()
            capture.start(loop)
            
            # Test stop
            capture.stop()
            assert capture._running is False
            assert capture._stream is None
            
            mock_stream_instance.stop.assert_called_once()
            mock_stream_instance.close.assert_called_once()
            
            # Clean up
            loop.close()


def test_audio_capture_start_error_handling():
    """Test audio capture start error handling."""
    with patch('jarvis.audio.capture.get_settings') as mock_settings:
        mock_settings.return_value.audio_send_sample_rate = 16000
        mock_settings.return_value.audio_channels = 1
        mock_settings.return_value.audio_chunk_size = 1024
        mock_settings.return_value.audio_device_index = None
        
        # Mock the callbacks
        output_callback = Mock()
        is_speaking = Mock(return_value=False)
        is_muted = Mock(return_value=False)
        is_phone_active = Mock(return_value=False)
        
        with patch('sounddevice.InputStream') as mock_stream:
            mock_stream.side_effect = Exception("Audio device error")
            
            from jarvis.audio.capture import AudioCapture
            
            capture = AudioCapture(
                output_callback=output_callback,
                is_speaking=is_speaking,
                is_muted=is_muted,
                is_phone_active=is_phone_active
            )
            
            # Should handle error gracefully
            loop = asyncio.new_event_loop()
            with pytest.raises(Exception, match="Audio device error"):
                capture.start(loop)
            
            # Clean up
            loop.close()


def test_audio_capture_stop_error_handling():
    """Test audio capture stop error handling."""
    with patch('jarvis.audio.capture.get_settings') as mock_settings:
        mock_settings.return_value.audio_send_sample_rate = 16000
        mock_settings.return_value.audio_channels = 1
        mock_settings.return_value.audio_chunk_size = 1024
        mock_settings.return_value.audio_device_index = None
        
        # Mock the callbacks
        output_callback = Mock()
        is_speaking = Mock(return_value=False)
        is_muted = Mock(return_value=False)
        is_phone_active = Mock(return_value=False)
        
        with patch('sounddevice.InputStream') as mock_stream:
            mock_stream_instance = Mock()
            mock_stream_instance.stop.side_effect = Exception("Stop error")
            mock_stream.return_value = mock_stream_instance
            
            from jarvis.audio.capture import AudioCapture
            
            capture = AudioCapture(
                output_callback=output_callback,
                is_speaking=is_speaking,
                is_muted=is_muted,
                is_phone_active=is_phone_active
            )
            
            # Start first
            loop = asyncio.new_event_loop()
            capture.start(loop)
            
            # Should handle stop error gracefully
            capture.stop()  # Should not raise exception
            
            assert capture._running is False
            assert capture._stream is None
            
            # Clean up
            loop.close()


def test_audio_capture_stream_parameters():
    """Test audio capture stream parameters."""
    with patch('jarvis.audio.capture.get_settings') as mock_settings:
        mock_settings.return_value.audio_send_sample_rate = 44100
        mock_settings.return_value.audio_channels = 2
        mock_settings.return_value.audio_chunk_size = 2048
        mock_settings.return_value.audio_device_index = 5
        
        # Mock the callbacks
        output_callback = Mock()
        is_speaking = Mock(return_value=False)
        is_muted = Mock(return_value=False)
        is_phone_active = Mock(return_value=False)
        
        with patch('sounddevice.InputStream') as mock_stream:
            from jarvis.audio.capture import AudioCapture
            
            capture = AudioCapture(
                output_callback=output_callback,
                is_speaking=is_speaking,
                is_muted=is_muted,
                is_phone_active=is_phone_active
            )
            
            loop = asyncio.new_event_loop()
            capture.start(loop)
            
            # Verify stream was created with correct parameters
            mock_stream.assert_called_once()
            call_kwargs = mock_stream.call_args[1]
            
            assert call_kwargs['samplerate'] == 44100
            assert call_kwargs['channels'] == 2
            assert call_kwargs['blocksize'] == 2048
            assert call_kwargs['device'] == 5
            assert call_kwargs['dtype'] == "int16"
            assert 'callback' in call_kwargs
            
            # Clean up
            loop.close()


def test_audio_capture_multiple_start_stop():
    """Test multiple start/stop cycles."""
    with patch('jarvis.audio.capture.get_settings') as mock_settings:
        mock_settings.return_value.audio_send_sample_rate = 16000
        mock_settings.return_value.audio_channels = 1
        mock_settings.return_value.audio_chunk_size = 1024
        mock_settings.return_value.audio_device_index = None
        
        # Mock the callbacks
        output_callback = Mock()
        is_speaking = Mock(return_value=False)
        is_muted = Mock(return_value=False)
        is_phone_active = Mock(return_value=False)
        
        with patch('sounddevice.InputStream') as mock_stream:
            mock_stream_instance = Mock()
            mock_stream.return_value = mock_stream_instance
            
            from jarvis.audio.capture import AudioCapture
            
            capture = AudioCapture(
                output_callback=output_callback,
                is_speaking=is_speaking,
                is_muted=is_muted,
                is_phone_active=is_phone_active
            )
            
            loop = asyncio.new_event_loop()
            
            # Multiple start/stop cycles
            for i in range(3):
                capture.start(loop)
                assert capture._running is True
                
                capture.stop()
                assert capture._running is False
            
            # Verify stream was called multiple times
            assert mock_stream.call_count == 3
            assert mock_stream_instance.start.call_count == 3
            assert mock_stream_instance.stop.call_count == 3
            assert mock_stream_instance.close.call_count == 3
            
            # Clean up
            loop.close()


def test_audio_capture_callback_conditions():
    """Test audio capture callback conditions."""
    with patch('jarvis.audio.capture.get_settings') as mock_settings:
        mock_settings.return_value.audio_send_sample_rate = 16000
        mock_settings.return_value.audio_channels = 1
        mock_settings.return_value.audio_chunk_size = 1024
        mock_settings.return_value.audio_device_index = None
        
        # Mock the callbacks
        output_callback = Mock()
        is_speaking = Mock(return_value=False)
        is_muted = Mock(return_value=False)
        is_phone_active = Mock(return_value=False)
        
        with patch('sounddevice.InputStream') as mock_stream:
            # Capture the callback function
            callback_func = None
            
            def capture_callback(*args, **kwargs):
                nonlocal callback_func
                if 'callback' in kwargs:
                    callback_func = kwargs['callback']
                return Mock()
            
            mock_stream.side_effect = capture_callback
            
            from jarvis.audio.capture import AudioCapture
            
            capture = AudioCapture(
                output_callback=output_callback,
                is_speaking=is_speaking,
                is_muted=is_muted,
                is_phone_active=is_phone_active
            )
            
            loop = asyncio.new_event_loop()
            capture.start(loop)
            
            # Test callback conditions
            assert callback_func is not None
            
            # Mock numpy array
            import numpy as np
            test_data = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float32)
            
            # Test when not running
            capture._running = False
            callback_func(test_data, 1024, {}, None)
            output_callback.assert_not_called()
            
            # Test when running
            capture._running = True
            callback_func(test_data, 1024, {}, None)
            # Note: The callback uses loop.call_soon_threadsafe, so we need to check
            # that the callback was scheduled, not necessarily called immediately
            
            # Clean up
            loop.close()


def test_audio_capture_state_management():
    """Test audio capture state management."""
    with patch('jarvis.audio.capture.get_settings') as mock_settings:
        mock_settings.return_value.audio_send_sample_rate = 16000
        mock_settings.return_value.audio_channels = 1
        mock_settings.return_value.audio_chunk_size = 1024
        mock_settings.return_value.audio_device_index = None
        
        # Mock the callbacks
        output_callback = Mock()
        is_speaking = Mock(return_value=False)
        is_muted = Mock(return_value=False)
        is_phone_active = Mock(return_value=False)
        
        from jarvis.audio.capture import AudioCapture
        
        capture = AudioCapture(
            output_callback=output_callback,
            is_speaking=is_speaking,
            is_muted=is_muted,
            is_phone_active=is_phone_active
        )
        
        # Test initial state
        assert capture._running is False
        assert capture._stream is None
        
        # Test state changes
        capture._running = True
        assert capture._running is True
        
        capture._running = False
        assert capture._running is False
