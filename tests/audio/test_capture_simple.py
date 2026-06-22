"""Simple tests for audio capture component."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
from typing import Any


def test_audio_capture_initialization():
    """Test audio capture initialization."""
    with patch('jarvis.audio.capture.get_settings') as mock_settings:
        mock_settings.return_value.audio_sample_rate = 16000
        mock_settings.return_value.audio_channels = 1
        
        from jarvis.audio.capture import AudioCapture
        capture = AudioCapture()
        
        assert capture is not None
        assert capture.sample_rate == 16000
        assert capture.channels == 1
        assert not capture._recording


def test_audio_capture_device_detection():
    """Test audio device detection."""
    with patch('jarvis.audio.capture.get_settings'):
        from jarvis.audio.capture import AudioCapture
        
        capture = AudioCapture()
        
        # Mock device detection
        with patch('sounddevice.query_devices') as mock_query:
            mock_query.return_value = [
                {'name': 'Default Device', 'max_input_channels': 2},
                {'name': 'Microphone', 'max_input_channels': 1}
            ]
            
            devices = capture.get_input_devices()
            assert len(devices) == 2
            assert devices[0]['name'] == 'Default Device'
            assert devices[1]['name'] == 'Microphone'


def test_audio_capture_start_stop():
    """Test audio capture start and stop."""
    with patch('jarvis.audio.capture.get_settings'):
        from jarvis.audio.capture import AudioCapture
        
        capture = AudioCapture()
        
        # Mock audio stream
        with patch('sounddevice.InputStream') as mock_stream:
            mock_stream_instance = Mock()
            mock_stream.return_value = mock_stream_instance
            
            # Start recording
            capture.start_recording()
            assert capture._recording
            mock_stream.assert_called_once()
            
            # Stop recording
            capture.stop_recording()
            assert not capture._recording
            mock_stream_instance.stop.assert_called_once()


def test_audio_capture_data_callback():
    """Test audio data callback."""
    with patch('jarvis.audio.capture.get_settings'):
        from jarvis.audio.capture import AudioCapture
        
        capture = AudioCapture()
        
        # Test data callback
        test_data = [0.1, 0.2, 0.3, 0.4]
        
        with patch.object(capture, '_process_audio_chunk') as mock_process:
            capture._audio_callback(test_data)
            mock_process.assert_called_once_with(test_data)


def test_audio_capture_format_validation():
    """Test audio format validation."""
    from jarvis.audio.capture import AudioCapture
    
    # Test valid formats
    valid_data = [0.1, 0.2, 0.3, 0.4]
    assert AudioCapture._validate_audio_data(valid_data)
    
    # Test invalid formats
    invalid_data = []
    assert not AudioCapture._validate_audio_data(invalid_data)
    
    invalid_data = [1.5, -1.5]  # Out of range
    assert not AudioCapture._validate_audio_data(invalid_data)


def test_audio_capture_buffer_management():
    """Test audio buffer management."""
    with patch('jarvis.audio.capture.get_settings'):
        from jarvis.audio.capture import AudioCapture
        
        capture = AudioCapture()
        
        # Add data to buffer
        chunk1 = [0.1, 0.2, 0.3, 0.4]
        chunk2 = [0.5, 0.6, 0.7, 0.8]
        
        capture._add_to_buffer(chunk1)
        capture._add_to_buffer(chunk2)
        
        assert len(capture._buffer) == 2
        
        # Get buffer data
        buffer_data = capture.get_buffer_data()
        assert len(buffer_data) == 8  # 2 chunks * 4 samples
        
        # Clear buffer
        capture.clear_buffer()
        assert len(capture._buffer) == 0


def test_audio_capture_error_handling():
    """Test error handling in audio capture."""
    with patch('jarvis.audio.capture.get_settings'):
        from jarvis.audio.capture import AudioCapture
        
        capture = AudioCapture()
        
        # Test device error
        with patch('sounddevice.InputStream') as mock_stream:
            mock_stream.side_effect = Exception("Device not found")
            
            try:
                capture.start_recording()
                assert False, "Should have raised exception"
            except Exception as e:
                assert "Device not found" in str(e)


def test_audio_capture_sample_rate_validation():
    """Test sample rate validation."""
    from jarvis.audio.capture import AudioCapture
    
    # Test valid sample rates
    valid_rates = [8000, 16000, 44100, 48000]
    for rate in valid_rates:
        assert AudioCapture._validate_sample_rate(rate)
    
    # Test invalid sample rates
    invalid_rates = [0, -1, 1000000]
    for rate in invalid_rates:
        assert not AudioCapture._validate_sample_rate(rate)


def test_audio_capture_channel_validation():
    """Test channel count validation."""
    from jarvis.audio.capture import AudioCapture
    
    # Test valid channel counts
    valid_channels = [1, 2]
    for channels in valid_channels:
        assert AudioCapture._validate_channels(channels)
    
    # Test invalid channel counts
    invalid_channels = [0, -1, 10]
    for channels in invalid_channels:
        assert not AudioCapture._validate_channels(channels)


def test_audio_capture_concurrent_operations():
    """Test concurrent audio operations."""
    with patch('jarvis.audio.capture.get_settings'):
        from jarvis.audio.capture import AudioCapture
        
        capture = AudioCapture()
        
        async def test_concurrent():
            with patch('sounddevice.InputStream') as mock_stream:
                mock_stream_instance = Mock()
                mock_stream.return_value = mock_stream_instance
                
                # Start recording
                capture.start_recording()
                
                # Simulate concurrent data processing
                tasks = []
                for i in range(5):
                    task = asyncio.create_task(capture._process_audio_async([0.1 * i]))
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks)
                assert len(results) == 5
                
                # Stop recording
                capture.stop_recording()
        
        asyncio.run(test_concurrent())


def test_audio_capture_metrics():
    """Test audio capture metrics."""
    with patch('jarvis.audio.capture.get_settings'):
        from jarvis.audio.capture import AudioCapture
        
        capture = AudioCapture()
        
        # Initial metrics
        metrics = capture.get_metrics()
        assert metrics["samples_captured"] == 0
        assert metrics["recording_time"] == 0
        assert metrics["buffer_size"] == 0
        
        # Update metrics
        capture._update_metrics("samples_captured", 1024)
        capture._update_metrics("recording_time", 1.5)
        
        metrics = capture.get_metrics()
        assert metrics["samples_captured"] == 1024
        assert metrics["recording_time"] == 1.5


def test_audio_capture_cleanup():
    """Test proper cleanup of audio resources."""
    with patch('jarvis.audio.capture.get_settings'):
        from jarvis.audio.capture import AudioCapture
        
        capture = AudioCapture()
        
        # Mock stream
        with patch('sounddevice.InputStream') as mock_stream:
            mock_stream_instance = Mock()
            mock_stream.return_value = mock_stream_instance
            
            # Start recording
            capture.start_recording()
            
            # Cleanup
            capture.cleanup()
            
            assert not capture._recording
            mock_stream_instance.stop.assert_called()
            mock_stream_instance.close.assert_called()


def test_audio_capture_configuration():
    """Test audio capture configuration."""
    with patch('jarvis.audio.capture.get_settings') as mock_settings:
        mock_settings.return_value.audio_sample_rate = 16000
        mock_settings.return_value.audio_channels = 1
        mock_settings.return_value.audio_buffer_size = 1024
        
        from jarvis.audio.capture import AudioCapture
        
        capture = AudioCapture()
        
        assert capture.sample_rate == 16000
        assert capture.channels == 1
        assert capture.buffer_size == 1024
