"""Tests for audio playback components."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import io


def test_audio_playback_initialization():
    """Test audio playback component initialization."""
    with patch('sounddevice.query_devices') as mock_query:
        mock_query.return_value = [
            {'name': 'Test Speaker', 'max_output_channels': 2, 'default_output_rate': 48000}
        ]
        
        from jarvis.audio.playback import AudioPlayback
        playback = AudioPlayback()
        
        assert playback is not None
        assert not playback.is_playing


def test_audio_playback_start_stop():
    """Test starting and stopping audio playback."""
    with patch('sounddevice.OutputStream') as mock_stream:
        mock_stream_instance = Mock()
        mock_stream.return_value = mock_stream_instance
        
        from jarvis.audio.playback import AudioPlayback
        playback = AudioPlayback()
        
        # Test data
        test_audio = np.random.random(1024).astype(np.float32)
        
        playback.play(test_audio)
        mock_stream.assert_called_once()
        assert playback.is_playing
        
        playback.stop()
        mock_stream_instance.stop.assert_called_once()
        assert not playback.is_playing


def test_audio_format_validation():
    """Test audio format validation for playback."""
    from jarvis.audio.playback import AudioPlayback
    
    # Valid formats
    valid_float32 = np.random.random(1024).astype(np.float32)
    valid_int16 = (np.random.random(1024) * 32767).astype(np.int16)
    
    assert AudioPlayback._validate_audio_format(valid_float32)
    assert AudioPlayback._validate_audio_format(valid_int16)
    
    # Invalid formats
    invalid_int8 = (np.random.random(1024) * 255).astype(np.int8)
    assert not AudioPlayback._validate_audio_format(invalid_int8)


def test_audio_volume_control():
    """Test audio volume control functionality."""
    with patch('sounddevice.OutputStream'):
        from jarvis.audio.playback import AudioPlayback
        playback = AudioPlayback()
        
        # Test volume setting
        playback.set_volume(0.5)
        assert playback.volume == 0.5
        
        # Test volume bounds
        playback.set_volume(1.5)  # Should clamp to 1.0
        assert playback.volume == 1.0
        
        playback.set_volume(-0.5)  # Should clamp to 0.0
        assert playback.volume == 0.0


def test_audio_resampling():
    """Test audio resampling functionality."""
    from jarvis.audio.playback import AudioPlayback
    
    # Create test audio at 16kHz
    original_rate = 16000
    target_rate = 48000
    duration = 1.0  # 1 second
    t = np.linspace(0, duration, int(original_rate * duration))
    original_audio = np.sin(2 * np.pi * 440 * t).astype(np.float32)
    
    # Resample to 48kHz
    resampled = AudioPlayback._resample_audio(original_audio, original_rate, target_rate)
    
    assert len(resampled) == int(target_rate * duration)
    assert resampled.dtype == np.float32


def test_audio_device_selection():
    """Test audio output device selection."""
    with patch('sounddevice.query_devices') as mock_query:
        mock_query.return_value = [
            {'name': 'Speaker 1', 'max_output_channels': 2, 'default_output_rate': 48000},
            {'name': 'Speaker 2', 'max_output_channels': 2, 'default_output_rate': 48000}
        ]
        
        from jarvis.audio.playback import AudioPlayback
        playback = AudioPlayback()
        
        # Select specific device
        success = playback.select_device('Speaker 2')
        assert success
        assert playback.selected_device == 'Speaker 2'
        
        # Try to select non-existent device
        success = playback.select_device('Non-existent')
        assert not success


def test_audio_queue_management():
    """Test audio playback queue management."""
    with patch('sounddevice.OutputStream'):
        from jarvis.audio.playback import AudioPlayback
        playback = AudioPlayback()
        
        # Add audio to queue
        test_audio1 = np.random.random(1024).astype(np.float32)
        test_audio2 = np.random.random(1024).astype(np.float32)
        
        playback.queue_audio(test_audio1)
        playback.queue_audio(test_audio2)
        
        assert len(playback._audio_queue) == 2
        
        # Clear queue
        playback.clear_queue()
        assert len(playback._audio_queue) == 0


def test_audio_callback_processing():
    """Test audio processing in playback callback."""
    with patch('sounddevice.OutputStream'):
        from jarvis.audio.playback import AudioPlayback
        playback = AudioPlayback()
        
        # Mock output buffer
        out_data = np.zeros((1024, 2), dtype=np.float32)
        frames = 1024
        time_info = {'outputBufferDacTime': 0.0}
        status = Mock()
        
        # Add test audio to queue
        test_audio = np.random.random(1024).astype(np.float32)
        playback.queue_audio(test_audio)
        
        # Process callback
        result = playback._audio_callback(out_data, frames, time_info, status)
        
        assert result is None  # Successful callback
        assert not np.allclose(out_data, 0)  # Data should be written


def test_audio_playback_with_no_devices():
    """Test behavior when no audio output devices are available."""
    with patch('sounddevice.query_devices') as mock_query:
        mock_query.return_value = []  # No devices
        
        from jarvis.audio.playback import AudioPlayback
        playback = AudioPlayback()
        
        devices = playback.get_output_devices()
        assert len(devices) == 0
        
        # Should handle gracefully when trying to play
        test_audio = np.random.random(1024).astype(np.float32)
        with pytest.raises(Exception):
            playback.play(test_audio)


def test_audio_stream_state_monitoring():
    """Test audio stream state monitoring."""
    with patch('sounddevice.OutputStream') as mock_stream:
        mock_stream_instance = Mock()
        mock_stream_instance.active = True
        mock_stream.return_value = mock_stream_instance
        
        from jarvis.audio.playback import AudioPlayback
        playback = AudioPlayback()
        
        test_audio = np.random.random(1024).astype(np.float32)
        playback.play(test_audio)
        
        assert playback.is_stream_active()
        
        mock_stream_instance.active = False
        assert not playback.is_stream_active()
