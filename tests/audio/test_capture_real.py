"""Real tests for audio capture component matching actual implementation."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
from typing import Any
import numpy as np


def test_audio_capture_initialization():
    """Test audio capture initialization with required callbacks."""
    mock_callback = Mock()
    mock_is_speaking = Mock(return_value=False)
    mock_is_muted = Mock(return_value=False)
    mock_is_phone_active = Mock(return_value=False)
    
    with patch('jarvis.audio.capture.get_settings') as mock_settings:
        mock_settings.return_value.audio_send_sample_rate = 16000
        mock_settings.return_value.audio_channels = 1
        mock_settings.return_value.audio_chunk_size = 1024
        mock_settings.return_value.audio_device_index = None
        
        from jarvis.audio.capture import AudioCapture
        capture = AudioCapture(
            output_callback=mock_callback,
            is_speaking=mock_is_speaking,
            is_muted=mock_is_muted,
            is_phone_active=mock_is_phone_active
        )
        
        assert capture is not None
        assert capture.output_callback == mock_callback
        assert capture.is_speaking == mock_is_speaking
        assert capture.is_muted == mock_is_muted
        assert capture.is_phone_active == mock_is_phone_active
        assert capture.settings == mock_settings.return_value
        assert not capture._running
        assert capture._stream is None


def test_audio_capture_start_stop():
    """Test audio capture start and stop functionality."""
    mock_callback = Mock()
    mock_is_speaking = Mock(return_value=False)
    mock_is_muted = Mock(return_value=False)
    mock_is_phone_active = Mock(return_value=False)
    
    with patch('jarvis.audio.capture.get_settings') as mock_settings:
        mock_settings.return_value.audio_send_sample_rate = 16000
        mock_settings.return_value.audio_channels = 1
        mock_settings.return_value.audio_chunk_size = 1024
        mock_settings.return_value.audio_device_index = None
        
        from jarvis.audio.capture import AudioCapture
        capture = AudioCapture(
            output_callback=mock_callback,
            is_speaking=mock_is_speaking,
            is_muted=mock_is_muted,
            is_phone_active=mock_is_phone_active
        )
        
        # Mock sounddevice
        with patch('sounddevice.InputStream') as mock_stream:
            mock_stream_instance = Mock()
            mock_stream.return_value = mock_stream_instance
            
            # Test start
            loop = asyncio.new_event_loop()
            capture.start(loop)
            
            assert capture._running
            mock_stream.assert_called_once()
            
            # Test stop
            capture.stop()
            assert not capture._running
            mock_stream_instance.stop.assert_called_once()
            
            loop.close()


def test_audio_capture_callback():
    """Test audio capture callback functionality."""
    mock_callback = Mock()
    mock_is_speaking = Mock(return_value=False)
    mock_is_muted = Mock(return_value=False)
    mock_is_phone_active = Mock(return_value=False)
    
    with patch('jarvis.audio.capture.get_settings') as mock_settings:
        mock_settings.return_value.audio_send_sample_rate = 16000
        mock_settings.return_value.audio_channels = 1
        mock_settings.return_value.audio_chunk_size = 1024
        mock_settings.return_value.audio_device_index = None
        
        from jarvis.audio.capture import AudioCapture
        capture = AudioCapture(
            output_callback=mock_callback,
            is_speaking=mock_is_speaking,
            is_muted=mock_is_muted,
            is_phone_active=mock_is_phone_active
        )
        
        # Mock audio data
        test_audio_data = np.array([[0.1, 0.2, 0.3, 0.4]], dtype=np.float32)
        
        # Test callback when running
        capture._running = True
        
        # Simulate the internal callback
        with patch('numpy.int16') as mock_int16:
            mock_int16.return_value = np.array([10, 20, 30, 40], dtype=np.int16)
            
            # Call the callback function
            capture._AudioCapture__callback(test_audio_data, 4, {}, None)
            
            # Should call output_callback
            mock_callback.assert_called()


def test_audio_capture_callback_conditions():
    """Test audio capture callback with various conditions."""
    mock_callback = Mock()
    mock_is_speaking = Mock(return_value=False)
    mock_is_muted = Mock(return_value=False)
    mock_is_phone_active = Mock(return_value=False)
    
    with patch('jarvis.audio.capture.get_settings') as mock_settings:
        mock_settings.return_value.audio_send_sample_rate = 16000
        mock_settings.return_value.audio_channels = 1
        mock_settings.return_value.audio_chunk_size = 1024
        mock_settings.return_value.audio_device_index = None
        
        from jarvis.audio.capture import AudioCapture
        capture = AudioCapture(
            output_callback=mock_callback,
            is_speaking=mock_is_speaking,
            is_muted=mock_is_muted,
            is_phone_active=mock_is_phone_active
        )
        
        test_audio_data = np.array([[0.1, 0.2, 0.3, 0.4]], dtype=np.float32)
        
        # Test when not running
        capture._running = False
        capture._AudioCapture__callback(test_audio_data, 4, {}, None)
        mock_callback.assert_not_called()
        
        # Test when speaking
        capture._running = True
        mock_is_speaking.return_value = True
        capture._AudioCapture__callback(test_audio_data, 4, {}, None)
        mock_callback.assert_not_called()
        
        # Test when muted
        mock_is_speaking.return_value = False
        mock_is_muted.return_value = True
        capture._AudioCapture__callback(test_audio_data, 4, {}, None)
        mock_callback.assert_not_called()
        
        # Test when phone active
        mock_is_muted.return_value = False
        mock_is_phone_active.return_value = True
        capture._AudioCapture__callback(test_audio_data, 4, {}, None)
        mock_callback.assert_not_called()


def test_audio_capture_error_handling():
    """Test error handling in audio capture."""
    mock_callback = Mock()
    mock_is_speaking = Mock(return_value=False)
    mock_is_muted = Mock(return_value=False)
    mock_is_phone_active = Mock(return_value=False)
    
    with patch('jarvis.audio.capture.get_settings') as mock_settings:
        mock_settings.return_value.audio_send_sample_rate = 16000
        mock_settings.return_value.audio_channels = 1
        mock_settings.return_value.audio_chunk_size = 1024
        mock_settings.return_value.audio_device_index = None
        
        from jarvis.audio.capture import AudioCapture
        capture = AudioCapture(
            output_callback=mock_callback,
            is_speaking=mock_is_speaking,
            is_muted=mock_is_muted,
            is_phone_active=mock_is_phone_active
        )
        
        # Test stream creation error
        with patch('sounddevice.InputStream') as mock_stream:
            mock_stream.side_effect = Exception("Audio device not found")
            
            loop = asyncio.new_event_loop()
            
            try:
                capture.start(loop)
                assert False, "Should have raised exception"
            except Exception as e:
                assert "Audio device not found" in str(e)
            finally:
                loop.close()


def test_audio_capture_configuration():
    """Test audio capture configuration handling."""
    mock_callback = Mock()
    mock_is_speaking = Mock(return_value=False)
    mock_is_muted = Mock(return_value=False)
    mock_is_phone_active = Mock(return_value=False)
    
    with patch('jarvis.audio.capture.get_settings') as mock_settings:
        mock_settings.return_value.audio_send_sample_rate = 48000
        mock_settings.return_value.audio_channels = 2
        mock_settings.return_value.audio_chunk_size = 2048
        mock_settings.return_value.audio_device_index = 1
        
        from jarvis.audio.capture import AudioCapture
        capture = AudioCapture(
            output_callback=mock_callback,
            is_speaking=mock_is_speaking,
            is_muted=mock_is_muted,
            is_phone_active=mock_is_phone_active
        )
        
        assert capture.settings.audio_send_sample_rate == 48000
        assert capture.settings.audio_channels == 2
        assert capture.settings.audio_chunk_size == 2048
        assert capture.settings.audio_device_index == 1


def test_audio_capture_custom_settings():
    """Test audio capture with custom settings."""
    mock_callback = Mock()
    mock_is_speaking = Mock(return_value=False)
    mock_is_muted = Mock(return_value=False)
    mock_is_phone_active = Mock(return_value=False)
    
    # Create custom settings
    custom_settings = Mock()
    custom_settings.audio_send_sample_rate = 44100
    custom_settings.audio_channels = 1
    custom_settings.audio_chunk_size = 512
    custom_settings.audio_device_index = None
    
    from jarvis.audio.capture import AudioCapture
    capture = AudioCapture(
        output_callback=mock_callback,
        is_speaking=mock_is_speaking,
        is_muted=mock_is_muted,
        is_phone_active=mock_is_phone_active,
        settings=custom_settings
    )
    
    assert capture.settings == custom_settings
    assert capture.settings.audio_send_sample_rate == 44100


def test_audio_capture_stream_parameters():
    """Test that stream is created with correct parameters."""
    mock_callback = Mock()
    mock_is_speaking = Mock(return_value=False)
    mock_is_muted = Mock(return_value=False)
    mock_is_phone_active = Mock(return_value=False)
    
    with patch('jarvis.audio.capture.get_settings') as mock_settings:
        mock_settings.return_value.audio_send_sample_rate = 16000
        mock_settings.return_value.audio_channels = 1
        mock_settings.return_value.audio_chunk_size = 1024
        mock_settings.return_value.audio_device_index = 2
        
        from jarvis.audio.capture import AudioCapture
        capture = AudioCapture(
            output_callback=mock_callback,
            is_speaking=mock_is_speaking,
            is_muted=mock_is_muted,
            is_phone_active=mock_is_phone_active
        )
        
        with patch('sounddevice.InputStream') as mock_stream:
            mock_stream_instance = Mock()
            mock_stream.return_value = mock_stream_instance
            
            loop = asyncio.new_event_loop()
            capture.start(loop)
            
            # Verify stream was called with correct parameters
            mock_stream.assert_called_once()
            call_args = mock_stream.call_args
            assert call_args[1]['samplerate'] == 16000
            assert call_args[1]['channels'] == 1
            assert call_args[1]['blocksize'] == 1024
            assert call_args[1]['device'] == 2
            
            capture.stop()
            loop.close()


def test_audio_capture_multiple_start_stop():
    """Test multiple start/stop cycles."""
    mock_callback = Mock()
    mock_is_speaking = Mock(return_value=False)
    mock_is_muted = Mock(return_value=False)
    mock_is_phone_active = Mock(return_value=False)
    
    with patch('jarvis.audio.capture.get_settings') as mock_settings:
        mock_settings.return_value.audio_send_sample_rate = 16000
        mock_settings.return_value.audio_channels = 1
        mock_settings.return_value.audio_chunk_size = 1024
        mock_settings.return_value.audio_device_index = None
        
        from jarvis.audio.capture import AudioCapture
        capture = AudioCapture(
            output_callback=mock_callback,
            is_speaking=mock_is_speaking,
            is_muted=mock_is_muted,
            is_phone_active=mock_is_phone_active
        )
        
        with patch('sounddevice.InputStream') as mock_stream:
            mock_stream_instance = Mock()
            mock_stream.return_value = mock_stream_instance
            
            loop = asyncio.new_event_loop()
            
            # Multiple start/stop cycles
            for i in range(3):
                capture.start(loop)
                assert capture._running
                capture.stop()
                assert not capture._running
            
            loop.close()


def test_audio_capture_callback_data_format():
    """Test that callback processes audio data correctly."""
    mock_callback = Mock()
    mock_is_speaking = Mock(return_value=False)
    mock_is_muted = Mock(return_value=False)
    mock_is_phone_active = Mock(return_value=False)
    
    with patch('jarvis.audio.capture.get_settings') as mock_settings:
        mock_settings.return_value.audio_send_sample_rate = 16000
        mock_settings.return_value.audio_channels = 1
        mock_settings.return_value.audio_chunk_size = 1024
        mock_settings.return_value.audio_device_index = None
        
        from jarvis.audio.capture import AudioCapture
        capture = AudioCapture(
            output_callback=mock_callback,
            is_speaking=mock_is_speaking,
            is_muted=mock_is_muted,
            is_phone_active=mock_is_phone_active
        )
        
        # Test with different audio data formats
        test_cases = [
            np.array([[0.1, 0.2, 0.3, 0.4]], dtype=np.float32),
            np.array([[-0.1, -0.2, -0.3, -0.4]], dtype=np.float32),
            np.array([[0.0, 0.0, 0.0, 0.0]], dtype=np.float32),
        ]
        
        capture._running = True
        
        for test_data in test_cases:
            with patch.object(test_data, 'astype') as mock_astype:
                mock_int16_array = np.array([10, 20, 30, 40], dtype=np.int16)
                mock_astype.return_value = mock_int16_array
                
                with patch.object(mock_int16_array, 'tobytes') as mock_tobytes:
                    mock_tobytes.return_value = b"audio_bytes"
                    
                    capture._AudioCapture__callback(test_data, 4, {}, None)
                    
                    # Should convert to int16 and then to bytes
                    mock_astype.assert_called_with(np.int16)
                    mock_tobytes.assert_called_once()
