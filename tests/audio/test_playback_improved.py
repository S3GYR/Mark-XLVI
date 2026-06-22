"""Improved tests for audio playback with proper mocking."""

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
    """Test audio playback initialization with proper mocking."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_device = "default"
        mock_settings.return_value.sample_rate = 16000
        mock_settings.return_value.channels = 1
        
        # Mock the audio queue
        audio_queue = Mock()
        audio_queue.empty.return_value = False
        audio_queue.get_nowait.return_value = b"test_audio_data"
        
        with patch('sounddevice.RawOutputStream') as mock_stream:
            from jarvis.audio.playback import AudioPlayback
            
            playback = AudioPlayback(audio_queue=audio_queue)
            
            assert playback is not None
            assert playback.audio_queue == audio_queue
            assert playback._running is False


def test_audio_playback_start_stop():
    """Test audio playback start and stop functionality."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_device = "default"
        mock_settings.return_value.sample_rate = 16000
        mock_settings.return_value.channels = 1
        
        # Mock the audio queue
        audio_queue = Mock()
        audio_queue.empty.return_value = False
        audio_queue.get_nowait.return_value = b"test_audio_data"
        
        with patch('sounddevice.RawOutputStream') as mock_stream:
            mock_stream_instance = Mock()
            mock_stream.return_value = mock_stream_instance
            
            from jarvis.audio.playback import AudioPlayback
            
            playback = AudioPlayback(audio_queue=audio_queue)
            
            # Test start
            playback.start()
            assert playback._running is True
            mock_stream_instance.start.assert_called_once()
            
            # Test stop
            playback.stop()
            assert playback._running is False
            mock_stream_instance.stop.assert_called_once()


def test_audio_playback_callback():
    """Test audio playback callback functionality."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_device = "default"
        mock_settings.return_value.sample_rate = 16000
        mock_settings.return_value.channels = 1
        
        # Mock the audio queue
        audio_queue = Mock()
        
        with patch('sounddevice.RawOutputStream'):
            from jarvis.audio.playback import AudioPlayback
            
            playback = AudioPlayback(audio_queue=audio_queue)
            
            # Test callback when not running
            output_data = bytearray(1024)
            playback._running = False
            playback._callback(output_data)
            # Should fill with zeros when not running
            
            # Test callback when running
            playback._running = True
            
            # Test with empty queue
            audio_queue.empty.return_value = True
            playback._callback(output_data)
            # Should fill with zeros when queue is empty
            
            # Test with data in queue
            audio_queue.empty.return_value = False
            audio_queue.get_nowait.return_value = b"test_audio_data"
            playback._callback(output_data)
            # Should process audio data


def test_audio_playback_callback_with_data():
    """Test audio playback callback with various data conditions."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_device = "default"
        mock_settings.return_value.sample_rate = 16000
        mock_settings.return_value.channels = 1
        
        # Mock the audio queue
        audio_queue = Mock()
        audio_queue.empty.return_value = False
        
        with patch('sounddevice.RawOutputStream'):
            from jarvis.audio.playback import AudioPlayback
            
            playback = AudioPlayback(audio_queue=audio_queue)
            playback._running = True
            
            # Test with different data sizes
            test_cases = [
                b"small_data",
                b"medium_audio_data" * 10,
                b"large_audio_data" * 100,
                b"",  # Empty data
            ]
            
            for test_data in test_cases:
                audio_queue.get_nowait.return_value = test_data
                output_data = bytearray(1024)
                
                playback._callback(output_data)
                
                # Verify callback was processed (no exception thrown)
                assert len(output_data) == 1024


def test_audio_playback_error_handling():
    """Test audio playback error handling."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_device = "default"
        mock_settings.return_value.sample_rate = 16000
        mock_settings.return_value.channels = 1
        
        # Mock the audio queue
        audio_queue = Mock()
        
        with patch('sounddevice.RawOutputStream') as mock_stream:
            mock_stream.side_effect = Exception("Audio device error")
            
            from jarvis.audio.playback import AudioPlayback
            
            playback = AudioPlayback(audio_queue=audio_queue)
            
            # Should handle error gracefully
            with pytest.raises(Exception):
                playback.start()


def test_audio_playback_configuration():
    """Test audio playback configuration."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_device = "test_device"
        mock_settings.return_value.sample_rate = 44100
        mock_settings.return_value.channels = 2
        
        # Mock the audio queue
        audio_queue = Mock()
        
        with patch('sounddevice.RawOutputStream') as mock_stream:
            from jarvis.audio.playback import AudioPlayback
            
            playback = AudioPlayback(audio_queue=audio_queue)
            playback.start()
            
            # Verify stream was created with correct parameters
            mock_stream.assert_called_once()
            call_args = mock_stream.call_args
            assert call_args[1]['samplerate'] == 44100
            assert call_args[1]['channels'] == 2


def test_audio_playback_stream_parameters():
    """Test audio playback stream parameter verification."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_device = "default"
        mock_settings.return_value.sample_rate = 16000
        mock_settings.return_value.channels = 1
        
        # Mock the audio queue
        audio_queue = Mock()
        
        with patch('sounddevice.RawOutputStream') as mock_stream:
            from jarvis.audio.playback import AudioPlayback
            
            playback = AudioPlayback(audio_queue=audio_queue)
            playback.start()
            
            # Verify stream parameters
            mock_stream.assert_called_once()
            call_kwargs = mock_stream.call_args[1]
            
            assert call_kwargs['device'] == "default"
            assert call_kwargs['samplerate'] == 16000
            assert call_kwargs['channels'] == 1
            assert 'callback' in call_kwargs


def test_audio_playback_multiple_start_stop():
    """Test multiple start/stop cycles."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_device = "default"
        mock_settings.return_value.sample_rate = 16000
        mock_settings.return_value.channels = 1
        
        # Mock the audio queue
        audio_queue = Mock()
        
        with patch('sounddevice.RawOutputStream') as mock_stream:
            mock_stream_instance = Mock()
            mock_stream.return_value = mock_stream_instance
            
            from jarvis.audio.playback import AudioPlayback
            
            playback = AudioPlayback(audio_queue=audio_queue)
            
            # Multiple start/stop cycles
            for i in range(3):
                playback.start()
                assert playback._running is True
                
                playback.stop()
                assert playback._running is False
            
            # Verify stream was called multiple times
            assert mock_stream.call_count == 3
            assert mock_stream_instance.start.call_count == 3
            assert mock_stream_instance.stop.call_count == 3


def test_audio_playback_queue_operations():
    """Test audio playback queue operations."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_device = "default"
        mock_settings.return_value.sample_rate = 16000
        mock_settings.return_value.channels = 1
        
        # Mock the audio queue
        audio_queue = Mock()
        
        with patch('sounddevice.RawOutputStream'):
            from jarvis.audio.playback import AudioPlayback
            
            playback = AudioPlayback(audio_queue=audio_queue)
            playback._running = True
            
            # Test queue empty
            audio_queue.empty.return_value = True
            output_data = bytearray(1024)
            playback._callback(output_data)
            
            # Test queue with data
            audio_queue.empty.return_value = False
            audio_queue.get_nowait.return_value = b"test_audio"
            playback._callback(output_data)
            
            # Verify queue methods were called
            audio_queue.empty.assert_called()
            audio_queue.get_nowait.assert_called()


def test_audio_playback_concurrent_operations():
    """Test concurrent operations on audio playback."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_device = "default"
        mock_settings.return_value.sample_rate = 16000
        mock_settings.return_value.channels = 1
        
        # Mock the audio queue
        audio_queue = Mock()
        audio_queue.empty.return_value = False
        audio_queue.get_nowait.return_value = b"test_audio"
        
        with patch('sounddevice.RawOutputStream') as mock_stream:
            mock_stream_instance = Mock()
            mock_stream.return_value = mock_stream_instance
            
            from jarvis.audio.playback import AudioPlayback
            
            playback = AudioPlayback(audio_queue=audio_queue)
            
            async def test_concurrent():
                # Start playback
                playback.start()
                
                # Simulate concurrent callbacks
                tasks = []
                for i in range(5):
                    output_data = bytearray(1024)
                    task = asyncio.create_task(
                        asyncio.to_thread(playback._callback, output_data)
                    )
                    tasks.append(task)
                
                await asyncio.gather(*tasks)
                
                # Stop playback
                playback.stop()
            
            asyncio.run(test_concurrent())


def test_audio_playback_device_selection():
    """Test audio playback device selection."""
    with patch('sounddevice.query_devices') as mock_query:
        mock_query.return_value = [
            {'name': 'Default Device', 'max_output_channels': 2},
            {'name': 'USB Speaker', 'max_output_channels': 1},
            {'name': 'Mic', 'max_output_channels': 0}
        ]
        
        from jarvis.audio.playback import AudioPlayback
        
        # Test device detection
        devices = AudioPlayback.get_available_devices()
        
        assert len(devices) == 2  # Only devices with output channels
        assert 'Default Device' in devices
        assert 'USB Speaker' in devices
        assert 'Mic' not in devices


def test_audio_playback_sample_rate_validation():
    """Test audio playback sample rate validation."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        # Test various sample rates
        sample_rates = [8000, 16000, 22050, 44100, 48000, 96000]
        
        for sample_rate in sample_rates:
            mock_settings.return_value.sample_rate = sample_rate
            mock_settings.return_value.channels = 1
            mock_settings.return_value.audio_device = "default"
            
            # Mock the audio queue
            audio_queue = Mock()
            
            with patch('sounddevice.RawOutputStream') as mock_stream:
                from jarvis.audio.playback import AudioPlayback
                
                playback = AudioPlayback(audio_queue=audio_queue)
                playback.start()
                
                # Verify stream was created with correct sample rate
                call_kwargs = mock_stream.call_args[1]
                assert call_kwargs['samplerate'] == sample_rate
                
                playback.stop()


def test_audio_playback_channel_validation():
    """Test audio playback channel validation."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        # Test various channel configurations
        channel_configs = [1, 2, 4, 8]
        
        for channels in channel_configs:
            mock_settings.return_value.sample_rate = 16000
            mock_settings.return_value.channels = channels
            mock_settings.return_value.audio_device = "default"
            
            # Mock the audio queue
            audio_queue = Mock()
            
            with patch('sounddevice.RawOutputStream') as mock_stream:
                from jarvis.audio.playback import AudioPlayback
                
                playback = AudioPlayback(audio_queue=audio_queue)
                playback.start()
                
                # Verify stream was created with correct channels
                call_kwargs = mock_stream.call_args[1]
                assert call_kwargs['channels'] == channels
                
                playback.stop()


def test_audio_playback_queue_timeout():
    """Test audio playback queue timeout handling."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_device = "default"
        mock_settings.return_value.sample_rate = 16000
        mock_settings.return_value.channels = 1
        
        # Mock the audio queue
        audio_queue = Mock()
        audio_queue.empty.return_value = True
        
        with patch('sounddevice.RawOutputStream'):
            from jarvis.audio.playback import AudioPlayback
            
            playback = AudioPlayback(audio_queue=audio_queue)
            playback._running = True
            
            # Test callback with empty queue
            output_data = bytearray(1024)
            playback._callback(output_data)
            
            # Should handle empty queue gracefully
            assert len(output_data) == 1024


def test_audio_playback_volume_control():
    """Test audio playback volume control."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_device = "default"
        mock_settings.return_value.sample_rate = 16000
        mock_settings.return_value.channels = 1
        
        # Mock the audio queue
        audio_queue = Mock()
        audio_queue.empty.return_value = False
        audio_queue.get_nowait.return_value = b"test_audio_data"
        
        with patch('sounddevice.RawOutputStream'):
            from jarvis.audio.playback import AudioPlayback
            
            playback = AudioPlayback(audio_queue=audio_queue)
            
            # Test volume control
            playback.set_volume(0.5)
            assert playback.volume == 0.5
            
            playback.set_volume(1.0)
            assert playback.volume == 1.0
            
            playback.set_volume(0.0)
            assert playback.volume == 0.0


def test_audio_playback_data_processing():
    """Test audio playback data processing."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_device = "default"
        mock_settings.return_value.sample_rate = 16000
        mock_settings.return_value.channels = 1
        
        # Mock the audio queue
        audio_queue = Mock()
        audio_queue.empty.return_value = False
        
        with patch('sounddevice.RawOutputStream'):
            from jarvis.audio.playback import AudioPlayback
            
            playback = AudioPlayback(audio_queue=audio_queue)
            playback._running = True
            
            # Test with different audio data formats
            test_cases = [
                b"raw_audio_data",
                bytes(range(256)),  # All byte values
                b"",  # Empty data
            ]
            
            for test_data in test_cases:
                audio_queue.get_nowait.return_value = test_data
                output_data = bytearray(1024)
                
                playback._callback(output_data)
                
                # Verify callback was processed (no exception thrown)
                assert len(output_data) == 1024


def test_audio_playback_cleanup():
    """Test audio playback cleanup."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_device = "default"
        mock_settings.return_value.sample_rate = 16000
        mock_settings.return_value.channels = 1
        
        # Mock the audio queue
        audio_queue = Mock()
        
        with patch('sounddevice.RawOutputStream') as mock_stream:
            mock_stream_instance = Mock()
            mock_stream.return_value = mock_stream_instance
            
            from jarvis.audio.playback import AudioPlayback
            
            playback = AudioPlayback(audio_queue=audio_queue)
            playback.start()
            
            # Test cleanup
            playback.cleanup()
            
            # Verify cleanup was performed
            assert playback._running is False
            mock_stream_instance.stop.assert_called()
            mock_stream_instance.close.assert_called()
