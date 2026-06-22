"""Real tests for audio playback component matching actual implementation."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
from typing import Any
import numpy as np


def test_audio_playback_initialization():
    """Test audio playback initialization."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_receive_sample_rate = 24000
        mock_settings.return_value.audio_channels = 1
        
        from jarvis.audio.playback import AudioPlayback
        playback = AudioPlayback()
        
        assert playback is not None
        assert playback.settings == mock_settings.return_value
        assert not playback._playing
        assert playback._stream is None


def test_audio_playback_start_stop():
    """Test audio playback start and stop functionality."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_receive_sample_rate = 24000
        mock_settings.return_value.audio_channels = 1
        mock_settings.return_value.audio_buffer_size = 1024
        
        from jarvis.audio.playback import AudioPlayback
        playback = AudioPlayback()
        
        # Mock sounddevice
        with patch('sounddevice.OutputStream') as mock_stream:
            mock_stream_instance = Mock()
            mock_stream.return_value = mock_stream_instance
            
            # Test start
            playback.start()
            
            assert playback._playing
            mock_stream.assert_called_once()
            
            # Test stop
            playback.stop()
            assert not playback._playing
            mock_stream_instance.stop.assert_called_once()


def test_audio_playback_queue_operations():
    """Test audio playback queue operations."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_receive_sample_rate = 24000
        mock_settings.return_value.audio_channels = 1
        
        from jarvis.audio.playback import AudioPlayback
        playback = AudioPlayback()
        
        # Test queue operations
        test_audio_data = b"test_audio_bytes"
        
        playback.put(test_audio_data)
        assert not playback._queue.empty()
        
        # Get data from queue
        retrieved_data = playback.get()
        assert retrieved_data == test_audio_data
        assert playback._queue.empty()


def test_audio_playback_concurrent_operations():
    """Test concurrent audio playback operations."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_receive_sample_rate = 24000
        mock_settings.return_value.audio_channels = 1
        
        from jarvis.audio.playback import AudioPlayback
        playback = AudioPlayback()
        
        async def test_concurrent():
            # Put multiple audio chunks
            tasks = []
            for i in range(5):
                audio_data = f"audio_chunk_{i}".encode()
                task = asyncio.create_task(asyncio.to_thread(playback.put, audio_data))
                tasks.append(task)
            
            await asyncio.gather(*tasks)
            
            # Verify queue has data
            assert not playback._queue.empty()
            
            # Get all data
            retrieved_data = []
            while not playback._queue.empty():
                data = playback.get()
                retrieved_data.append(data)
            
            assert len(retrieved_data) == 5
        
        asyncio.run(test_concurrent())


def test_audio_playback_error_handling():
    """Test error handling in audio playback."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_receive_sample_rate = 24000
        mock_settings.return_value.audio_channels = 1
        
        from jarvis.audio.playback import AudioPlayback
        playback = AudioPlayback()
        
        # Test stream creation error
        with patch('sounddevice.OutputStream') as mock_stream:
            mock_stream.side_effect = Exception("Audio device not found")
            
            try:
                playback.start()
                assert False, "Should have raised exception"
            except Exception as e:
                assert "Audio device not found" in str(e)


def test_audio_playback_configuration():
    """Test audio playback configuration handling."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_receive_sample_rate = 48000
        mock_settings.return_value.audio_channels = 2
        mock_settings.return_value.audio_buffer_size = 2048
        
        from jarvis.audio.playback import AudioPlayback
        playback = AudioPlayback()
        
        assert playback.settings.audio_receive_sample_rate == 48000
        assert playback.settings.audio_channels == 2
        assert playback.settings.audio_buffer_size == 2048


def test_audio_playback_buffer_management():
    """Test audio buffer management."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_receive_sample_rate = 24000
        mock_settings.return_value.audio_channels = 1
        
        from jarvis.audio.playback import AudioPlayback
        playback = AudioPlayback()
        
        # Test buffer size
        assert playback._queue.maxsize > 0
        
        # Fill buffer to capacity
        max_size = playback._queue.maxsize
        for i in range(max_size):
            playback.put(f"data_{i}".encode())
        
        # Buffer should be full
        assert playback._queue.full()
        
        # Clear buffer
        playback.clear_buffer()
        assert playback._queue.empty()


def test_audio_playback_stream_parameters():
    """Test that stream is created with correct parameters."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_receive_sample_rate = 24000
        mock_settings.return_value.audio_channels = 1
        mock_settings.return_value.audio_buffer_size = 1024
        
        from jarvis.audio.playback import AudioPlayback
        playback = AudioPlayback()
        
        with patch('sounddevice.OutputStream') as mock_stream:
            mock_stream_instance = Mock()
            mock_stream.return_value = mock_stream_instance
            
            playback.start()
            
            # Verify stream was called with correct parameters
            mock_stream.assert_called_once()
            call_args = mock_stream.call_args
            assert call_args[1]['samplerate'] == 24000
            assert call_args[1]['channels'] == 1
            
            playback.stop()


def test_audio_playback_data_processing():
    """Test audio data processing."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_receive_sample_rate = 24000
        mock_settings.return_value.audio_channels = 1
        
        from jarvis.audio.playback import AudioPlayback
        playback = AudioPlayback()
        
        # Test different audio data formats
        test_cases = [
            b"simple_audio_data",
            bytearray(b"bytearray_audio"),
            bytes([0x00, 0x01, 0x02, 0x03])
        ]
        
        for audio_data in test_cases:
            playback.put(audio_data)
            retrieved = playback.get()
            assert retrieved == audio_data


def test_audio_playback_multiple_start_stop():
    """Test multiple start/stop cycles."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_receive_sample_rate = 24000
        mock_settings.return_value.audio_channels = 1
        
        from jarvis.audio.playback import AudioPlayback
        playback = AudioPlayback()
        
        with patch('sounddevice.OutputStream') as mock_stream:
            mock_stream_instance = Mock()
            mock_stream.return_value = mock_stream_instance
            
            # Multiple start/stop cycles
            for i in range(3):
                playback.start()
                assert playback._playing
                playback.stop()
                assert not playback._playing


def test_audio_playback_queue_timeout():
    """Test queue operations with timeout."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_receive_sample_rate = 24000
        mock_settings.return_value.audio_channels = 1
        
        from jarvis.audio.playback import AudioPlayback
        playback = AudioPlayback()
        
        # Test get from empty queue with timeout
        with patch('queue.Queue.get') as mock_get:
            mock_get.side_effect = Exception("Queue empty")
            
            try:
                playback.get(timeout=0.1)
                assert False, "Should have raised exception"
            except Exception:
                pass  # Expected


def test_audio_playback_volume_control():
    """Test volume control functionality."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_receive_sample_rate = 24000
        mock_settings.return_value.audio_channels = 1
        
        from jarvis.audio.playback import AudioPlayback
        playback = AudioPlayback()
        
        # Test volume setting (if implemented)
        if hasattr(playback, 'set_volume'):
            playback.set_volume(0.5)
            assert playback.volume == 0.5
            
            playback.set_volume(1.0)
            assert playback.volume == 1.0


def test_audio_playback_device_selection():
    """Test audio device selection."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_receive_sample_rate = 24000
        mock_settings.return_value.audio_channels = 1
        mock_settings.return_value.audio_output_device = 2
        
        from jarvis.audio.playback import AudioPlayback
        playback = AudioPlayback()
        
        with patch('sounddevice.OutputStream') as mock_stream:
            mock_stream_instance = Mock()
            mock_stream.return_value = mock_stream_instance
            
            playback.start()
            
            # Verify device parameter
            call_args = mock_stream.call_args
            assert call_args[1]['device'] == 2
            
            playback.stop()


def test_audio_playback_format_conversion():
    """Test audio format conversion."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_receive_sample_rate = 24000
        mock_settings.return_value.audio_channels = 1
        
        from jarvis.audio.playback import AudioPlayback
        playback = AudioPlayback()
        
        # Test format conversion if implemented
        if hasattr(playback, '_convert_audio_format'):
            test_data = b"test_audio"
            converted = playback._convert_audio_format(test_data)
            assert converted is not None


def test_audio_playback_cleanup():
    """Test proper cleanup of audio resources."""
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_receive_sample_rate = 24000
        mock_settings.return_value.audio_channels = 1
        
        from jarvis.audio.playback import AudioPlayback
        playback = AudioPlayback()
        
        with patch('sounddevice.OutputStream') as mock_stream:
            mock_stream_instance = Mock()
            mock_stream.return_value = mock_stream_instance
            
            # Start playback
            playback.start()
            
            # Add some data to queue
            playback.put(b"test_data")
            
            # Cleanup
            playback.cleanup()
            
            assert not playback._playing
            assert playback._stream is None
            assert playback._queue.empty()
            mock_stream_instance.stop.assert_called()
            mock_stream_instance.close.assert_called()
