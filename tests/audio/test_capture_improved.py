"""Improved tests for audio capture with proper mocking."""

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
    """Test audio capture initialization with proper mocking."""
    with patch('jarvis.audio.capture.get_settings') as mock_settings:
        mock_settings.return_value.audio_device = "default"
        mock_settings.return_value.sample_rate = 16000
        mock_settings.return_value.channels = 1
        
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
            
            assert capture is not None
            assert capture.output_callback == output_callback
            assert capture._running is False


def test_audio_capture_start_stop():
    """Test audio capture start and stop functionality."""
    with patch('jarvis.audio.capture.get_settings') as mock_settings:
        mock_settings.return_value.audio_device = "default"
        mock_settings.return_value.sample_rate = 16000
        mock_settings.return_value.channels = 1
        
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
            
            # Test start
            capture.start()
            assert capture._running is True
            mock_stream_instance.start.assert_called_once()
            
            # Test stop
            capture.stop()
            assert capture._running is False
            mock_stream_instance.stop.assert_called_once()


def test_audio_capture_callback():
    """Test audio capture callback functionality."""
    with patch('jarvis.audio.capture.get_settings') as mock_settings:
        mock_settings.return_value.audio_device = "default"
        mock_settings.return_value.sample_rate = 16000
        mock_settings.return_value.channels = 1
        
        # Mock the callbacks
        output_callback = Mock()
        is_speaking = Mock(return_value=False)
        is_muted = Mock(return_value=False)
        is_phone_active = Mock(return_value=False)
        
        with patch('sounddevice.InputStream'):
            from jarvis.audio.capture import AudioCapture
            
            capture = AudioCapture(
                output_callback=output_callback,
                is_speaking=is_speaking,
                is_muted=is_muted,
                is_phone_active=is_phone_active
            )
            
            # Test callback when not running
            test_data = [1, 2, 3, 4, 5]
            capture._running = False
            capture._callback(test_data)
            output_callback.assert_not_called()
            
            # Test callback when running
            capture._running = True
            capture._callback(test_data)
            output_callback.assert_called_once()


def test_audio_capture_callback_with_conditions():
    """Test audio capture callback under various conditions."""
    with patch('jarvis.audio.capture.get_settings') as mock_settings:
        mock_settings.return_value.audio_device = "default"
        mock_settings.return_value.sample_rate = 16000
        mock_settings.return_value.channels = 1
        
        # Mock the callbacks
        output_callback = Mock()
        is_speaking = Mock(return_value=False)
        is_muted = Mock(return_value=False)
        is_phone_active = Mock(return_value=False)
        
        with patch('sounddevice.InputStream'):
            from jarvis.audio.capture import AudioCapture
            
            capture = AudioCapture(
                output_callback=output_callback,
                is_speaking=is_speaking,
                is_muted=is_muted,
                is_phone_active=is_phone_active
            )
            
            capture._running = True
            
            # Test when speaking
            is_speaking.return_value = True
            capture._callback([1, 2, 3])
            output_callback.assert_not_called()
            
            # Reset
            output_callback.reset_mock()
            is_speaking.return_value = False
            
            # Test when muted
            is_muted.return_value = True
            capture._callback([1, 2, 3])
            output_callback.assert_not_called()
            
            # Reset
            output_callback.reset_mock()
            is_muted.return_value = False
            
            # Test when phone active
            is_phone_active.return_value = True
            capture._callback([1, 2, 3])
            output_callback.assert_not_called()
            
            # Reset
            output_callback.reset_mock()
            is_phone_active.return_value = False
            
            # Test normal operation
            capture._callback([1, 2, 3])
            output_callback.assert_called_once()


def test_audio_capture_error_handling():
    """Test audio capture error handling."""
    with patch('jarvis.audio.capture.get_settings') as mock_settings:
        mock_settings.return_value.audio_device = "default"
        mock_settings.return_value.sample_rate = 16000
        mock_settings.return_value.channels = 1
        
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
            with pytest.raises(Exception):
                capture.start()


def test_audio_capture_configuration():
    """Test audio capture configuration."""
    with patch('jarvis.audio.capture.get_settings') as mock_settings:
        mock_settings.return_value.audio_device = "test_device"
        mock_settings.return_value.sample_rate = 44100
        mock_settings.return_value.channels = 2
        mock_settings.return_value.block_size = 1024
        
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
            
            capture.start()
            
            # Verify stream was created with correct parameters
            mock_stream.assert_called_once()
            call_args = mock_stream.call_args
            assert call_args[1]['samplerate'] == 44100
            assert call_args[1]['channels'] == 2
            assert call_args[1]['blocksize'] == 1024


def test_audio_capture_stream_parameters():
    """Test audio capture stream parameter verification."""
    with patch('jarvis.audio.capture.get_settings') as mock_settings:
        mock_settings.return_value.audio_device = "default"
        mock_settings.return_value.sample_rate = 16000
        mock_settings.return_value.channels = 1
        mock_settings.return_value.block_size = 512
        
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
            
            capture.start()
            
            # Verify stream parameters
            mock_stream.assert_called_once()
            call_kwargs = mock_stream.call_args[1]
            
            assert call_kwargs['device'] == "default"
            assert call_kwargs['samplerate'] == 16000
            assert call_kwargs['channels'] == 1
            assert call_kwargs['blocksize'] == 512
            assert 'callback' in call_kwargs


def test_audio_capture_multiple_start_stop():
    """Test multiple start/stop cycles."""
    with patch('jarvis.audio.capture.get_settings') as mock_settings:
        mock_settings.return_value.audio_device = "default"
        mock_settings.return_value.sample_rate = 16000
        mock_settings.return_value.channels = 1
        
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
            
            # Multiple start/stop cycles
            for i in range(3):
                capture.start()
                assert capture._running is True
                
                capture.stop()
                assert capture._running is False
            
            # Verify stream was called multiple times
            assert mock_stream.call_count == 3
            assert mock_stream_instance.start.call_count == 3
            assert mock_stream_instance.stop.call_count == 3


def test_audio_capture_callback_data_processing():
    """Test audio capture callback data processing."""
    with patch('jarvis.audio.capture.get_settings') as mock_settings:
        mock_settings.return_value.audio_device = "default"
        mock_settings.return_value.sample_rate = 16000
        mock_settings.return_value.channels = 1
        
        # Mock the callbacks
        output_callback = Mock()
        is_speaking = Mock(return_value=False)
        is_muted = Mock(return_value=False)
        is_phone_active = Mock(return_value=False)
        
        with patch('sounddevice.InputStream'):
            from jarvis.audio.capture import AudioCapture
            
            capture = AudioCapture(
                output_callback=output_callback,
                is_speaking=is_speaking,
                is_muted=is_muted,
                is_phone_active=is_phone_active
            )
            
            capture._running = True
            
            # Test with different data types
            test_cases = [
                [1, 2, 3, 4, 5],
                [0.1, 0.2, 0.3, 0.4, 0.5],
                [-1, -2, -3, -4, -5],
                []
            ]
            
            for test_data in test_cases:
                output_callback.reset_mock()
                capture._callback(test_data)
                
                if test_data:  # Non-empty data should trigger callback
                    output_callback.assert_called_once()
                    # Verify the callback was called with processed data
                    args = output_callback.call_args[0]
                    assert len(args) == 1
                    assert isinstance(args[0], bytes)
                else:  # Empty data might not trigger callback
                    pass


def test_audio_capture_concurrent_operations():
    """Test concurrent operations on audio capture."""
    with patch('jarvis.audio.capture.get_settings') as mock_settings:
        mock_settings.return_value.audio_device = "default"
        mock_settings.return_value.sample_rate = 16000
        mock_settings.return_value.channels = 1
        
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
            
            async def test_concurrent():
                # Start capture
                capture.start()
                
                # Simulate concurrent callbacks
                tasks = []
                for i in range(5):
                    task = asyncio.create_task(
                        asyncio.to_thread(capture._callback, [i, i+1, i+2])
                    )
                    tasks.append(task)
                
                await asyncio.gather(*tasks)
                
                # Stop capture
                capture.stop()
                
                # Verify callbacks were called
                assert output_callback.call_count > 0
            
            asyncio.run(test_concurrent())


def test_audio_capture_device_detection():
    """Test audio capture device detection."""
    with patch('sounddevice.query_devices') as mock_query:
        mock_query.return_value = [
            {'name': 'Default Device', 'max_input_channels': 2},
            {'name': 'USB Mic', 'max_input_channels': 1},
            {'name': 'Speaker', 'max_input_channels': 0}
        ]
        
        from jarvis.audio.capture import AudioCapture
        
        # Test device detection
        devices = AudioCapture.get_available_devices()
        
        assert len(devices) == 2  # Only devices with input channels
        assert 'Default Device' in devices
        assert 'USB Mic' in devices
        assert 'Speaker' not in devices


def test_audio_capture_sample_rate_validation():
    """Test audio capture sample rate validation."""
    with patch('jarvis.audio.capture.get_settings') as mock_settings:
        # Test various sample rates
        sample_rates = [8000, 16000, 22050, 44100, 48000, 96000]
        
        for sample_rate in sample_rates:
            mock_settings.return_value.sample_rate = sample_rate
            mock_settings.return_value.channels = 1
            mock_settings.return_value.audio_device = "default"
            
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
                
                capture.start()
                
                # Verify stream was created with correct sample rate
                call_kwargs = mock_stream.call_args[1]
                assert call_kwargs['samplerate'] == sample_rate
                
                capture.stop()


def test_audio_capture_channel_validation():
    """Test audio capture channel validation."""
    with patch('jarvis.audio.capture.get_settings') as mock_settings:
        # Test various channel configurations
        channel_configs = [1, 2, 4, 8]
        
        for channels in channel_configs:
            mock_settings.return_value.sample_rate = 16000
            mock_settings.return_value.channels = channels
            mock_settings.return_value.audio_device = "default"
            
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
                
                capture.start()
                
                # Verify stream was created with correct channels
                call_kwargs = mock_stream.call_args[1]
                assert call_kwargs['channels'] == channels
                
                capture.stop()
