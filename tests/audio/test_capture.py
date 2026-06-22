"""Tests for audio capture components."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np


def test_audio_device_detection():
    """Test audio device detection functionality."""
    with patch('sounddevice.query_devices') as mock_query:
        mock_query.return_value = [
            {'name': 'Test Mic', 'max_input_channels': 2, 'default_input_rate': 16000},
            {'name': 'Test Speaker', 'max_output_channels': 2, 'default_output_rate': 48000}
        ]
        
        from jarvis.audio.capture import AudioCapture
        capture = AudioCapture()
        
        devices = capture.get_input_devices()
        assert len(devices) > 0
        assert 'Test Mic' in [d['name'] for d in devices]


def test_audio_capture_start_stop():
    """Test starting and stopping audio capture."""
    with patch('sounddevice.InputStream') as mock_stream:
        mock_stream_instance = Mock()
        mock_stream.return_value = mock_stream_instance
        
        from jarvis.audio.capture import AudioCapture
        capture = AudioCapture()
        
        capture.start()
        mock_stream.assert_called_once()
        assert capture.is_recording
        
        capture.stop()
        mock_stream_instance.stop.assert_called_once()
        assert not capture.is_recording


def test_audio_callback_processing():
    """Test audio data processing in callback."""
    with patch('sounddevice.InputStream'):
        from jarvis.audio.capture import AudioCapture
        capture = AudioCapture()
        
        # Mock audio data
        test_data = np.random.randint(-32768, 32767, (1024, 1), dtype=np.int16)
        
        # Process the data
        processed = capture._process_audio_data(test_data)
        
        assert processed is not None
        assert len(processed.shape) == 1  # Should be 1D after processing


def test_audio_format_conversion():
    """Test audio format conversion utilities."""
    from jarvis.audio.capture import AudioCapture
        
    # Test int16 to float32 conversion
    int16_data = np.array([1000, -1000, 0], dtype=np.int16)
    float32_data = AudioCapture._to_float32(int16_data)
    
    assert float32_data.dtype == np.float32
    assert len(float32_data) == len(int16_data)
    assert float32_data[0] > 0  # Positive value
    assert float32_data[1] < 0  # Negative value


def test_audio_buffer_management():
    """Test audio buffer management."""
    with patch('sounddevice.InputStream'):
        from jarvis.audio.capture import AudioCapture
        capture = AudioCapture()
        
        # Add data to buffer
        test_data = np.random.randint(-32768, 32767, (1024, 1), dtype=np.int16)
        capture._add_to_buffer(test_data)
        
        # Check buffer size
        assert len(capture._buffer) > 0
        
        # Clear buffer
        capture._clear_buffer()
        assert len(capture._buffer) == 0


def test_audio_capture_with_no_devices():
    """Test behavior when no audio devices are available."""
    with patch('sounddevice.query_devices') as mock_query:
        mock_query.return_value = []  # No devices
        
        from jarvis.audio.capture import AudioCapture
        capture = AudioCapture()
        
        devices = capture.get_input_devices()
        assert len(devices) == 0
        
        # Should handle gracefully when trying to start
        with pytest.raises(Exception):
            capture.start()


def test_audio_sample_rate_validation():
    """Test sample rate validation."""
    from jarvis.audio.capture import AudioCapture
    
    # Valid sample rates
    assert AudioCapture._is_valid_sample_rate(16000)
    assert AudioCapture._is_valid_sample_rate(44100)
    assert AudioCapture._is_valid_sample_rate(48000)
    
    # Invalid sample rates
    assert not AudioCapture._is_valid_sample_rate(8000)
    assert not AudioCapture._is_valid_sample_rate(96000)


def test_audio_device_selection():
    """Test audio device selection by name."""
    with patch('sounddevice.query_devices') as mock_query:
        mock_query.return_value = [
            {'name': 'Mic 1', 'max_input_channels': 2, 'default_input_rate': 16000},
            {'name': 'Mic 2', 'max_input_channels': 2, 'default_input_rate': 16000}
        ]
        
        from jarvis.audio.capture import AudioCapture
        capture = AudioCapture()
        
        # Select specific device
        success = capture.select_device('Mic 2')
        assert success
        assert capture.selected_device == 'Mic 2'
        
        # Try to select non-existent device
        success = capture.select_device('Non-existent')
        assert not success
