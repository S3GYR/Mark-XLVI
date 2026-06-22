"""Fixed tests for audio playback component matching actual implementation."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
from typing import Any
import numpy as np


def test_audio_playback_initialization():
    """Test audio playback initialization with required audio queue."""
    mock_audio_queue = Mock()
    mock_audio_queue.get_nowait.side_effect = Exception("Queue empty")
    
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_receive_sample_rate = 24000
        mock_settings.return_value.audio_channels = 1
        mock_settings.return_value.audio_chunk_size = 1024
        
        from jarvis.audio.playback import AudioPlayback
        playback = AudioPlayback(audio_queue=mock_audio_queue)
        
        assert playback is not None
        assert playback.audio_queue == mock_audio_queue
        assert playback.settings == mock_settings.return_value
        assert not playback._running
        assert playback._stream is None


def test_audio_playback_start_stop():
    """Test audio playback start and stop functionality."""
    mock_audio_queue = Mock()
    mock_audio_queue.get_nowait.side_effect = Exception("Queue empty")
    
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_receive_sample_rate = 24000
        mock_settings.return_value.audio_channels = 1
        mock_settings.return_value.audio_chunk_size = 1024
        
        from jarvis.audio.playback import AudioPlayback
        playback = AudioPlayback(audio_queue=mock_audio_queue)
        
        # Mock sounddevice
        with patch('sounddevice.RawOutputStream') as mock_stream:
            mock_stream_instance = Mock()
            mock_stream.return_value = mock_stream_instance
            
            # Test start
            playback.start()
            
            assert playback._running
            mock_stream.assert_called_once()
            
            # Test stop
            playback.stop()
            assert not playback._running
            mock_stream_instance.stop.assert_called_once()


def test_audio_playback_callback():
    """Test audio playback callback functionality."""
    mock_audio_queue = Mock()
    
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_receive_sample_rate = 24000
        mock_settings.return_value.audio_channels = 1
        mock_settings.return_value.audio_chunk_size = 1024
        
        from jarvis.audio.playback import AudioPlayback
        playback = AudioPlayback(audio_queue=mock_audio_queue)
        
        # Test callback when not running
        playback._running = False
        outdata = np.zeros((1024, 1), dtype=np.int16)
        
        playback._AudioPlayback__callback(outdata, 1024, {}, None)
        
        # Should fill with zeros when not running
        assert np.all(outdata == 0)
        
        # Test callback when running but queue empty
        playback._running = True
        mock_audio_queue.get_nowait.side_effect = asyncio.QueueEmpty()
        
        playback._AudioPlayback__callback(outdata, 1024, {}, None)
        
        # Should fill with zeros when queue empty
        assert np.all(outdata == 0)


def test_audio_playback_callback_with_data():
    """Test audio playback callback with audio data."""
    mock_audio_queue = Mock()
    
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_receive_sample_rate = 24000
        mock_settings.return_value.audio_channels = 1
        mock_settings.return_value.audio_chunk_size = 1024
        
        from jarvis.audio.playback import AudioPlayback
        playback = AudioPlayback(audio_queue=mock_audio_queue)
        
        # Test with exact size data
        playback._running = True
        test_data = b"\x01\x02" * 1024  # 2048 bytes = 1024 frames * 2 bytes
        mock_audio_queue.get_nowait.return_value = test_data
        
        outdata = np.zeros((1024, 1), dtype=np.int16)
        playback._AudioPlayback__callback(outdata, 1024, {}, None)
        
        # Should fill with audio data
        assert not np.all(outdata == 0)
        mock_audio_queue.get_nowait.assert_called_once()


def test_audio_playback_callback_with_undersized_data():
    """Test audio playback callback with undersized audio data."""
    mock_audio_queue = Mock()
    
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_receive_sample_rate = 24000
        mock_settings.return_value.audio_channels = 1
        mock_settings.return_value.audio_chunk_size = 1024
        
        from jarvis.audio.playback import AudioPlayback
        playback = AudioPlayback(audio_queue=mock_audio_queue)
        
        # Test with undersized data
        playback._running = True
        test_data = b"\x01\x02" * 512  # 1024 bytes = 512 frames * 2 bytes
        mock_audio_queue.get_nowait.return_value = test_data
        
        outdata = np.zeros((1024, 1), dtype=np.int16)
        playback._AudioPlayback__callback(outdata, 1024, {}, None)
        
        # Should fill first part with data, rest with zeros
        assert not np.all(outdata[:512] == 0)  # First part has data
        assert np.all(outdata[512:] == 0)  # Second part is zeros


def test_audio_playback_error_handling():
    """Test error handling in audio playback."""
    mock_audio_queue = Mock()
    mock_audio_queue.get_nowait.side_effect = Exception("Queue empty")
    
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_receive_sample_rate = 24000
        mock_settings.return_value.audio_channels = 1
        mock_settings.return_value.audio_chunk_size = 1024
        
        from jarvis.audio.playback import AudioPlayback
        playback = AudioPlayback(audio_queue=mock_audio_queue)
        
        # Test stream creation error
        with patch('sounddevice.RawOutputStream') as mock_stream:
            mock_stream.side_effect = Exception("Audio device not found")
            
            try:
                playback.start()
                assert False, "Should have raised exception"
            except Exception as e:
                assert "Audio device not found" in str(e)


def test_audio_playback_configuration():
    """Test audio playback configuration handling."""
    mock_audio_queue = Mock()
    mock_audio_queue.get_nowait.side_effect = Exception("Queue empty")
    
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_receive_sample_rate = 48000
        mock_settings.return_value.audio_channels = 2
        mock_settings.return_value.audio_chunk_size = 2048
        
        from jarvis.audio.playback import AudioPlayback
        playback = AudioPlayback(audio_queue=mock_audio_queue)
        
        assert playback.settings.audio_receive_sample_rate == 48000
        assert playback.settings.audio_channels == 2
        assert playback.settings.audio_chunk_size == 2048


def test_audio_playback_stream_parameters():
    """Test that stream is created with correct parameters."""
    mock_audio_queue = Mock()
    mock_audio_queue.get_nowait.side_effect = Exception("Queue empty")
    
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_receive_sample_rate = 24000
        mock_settings.return_value.audio_channels = 1
        mock_settings.return_value.audio_chunk_size = 1024
        
        from jarvis.audio.playback import AudioPlayback
        playback = AudioPlayback(audio_queue=mock_audio_queue)
        
        with patch('sounddevice.RawOutputStream') as mock_stream:
            mock_stream_instance = Mock()
            mock_stream.return_value = mock_stream_instance
            
            playback.start()
            
            # Verify stream was called with correct parameters
            mock_stream.assert_called_once()
            call_args = mock_stream.call_args
            assert call_args[1]['samplerate'] == 24000
            assert call_args[1]['channels'] == 1
            assert call_args[1]['blocksize'] == 1024
            assert call_args[1]['dtype'] == 'int16'
            
            playback.stop()


def test_audio_playback_multiple_start_stop():
    """Test multiple start/stop cycles."""
    mock_audio_queue = Mock()
    mock_audio_queue.get_nowait.side_effect = Exception("Queue empty")
    
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_receive_sample_rate = 24000
        mock_settings.return_value.audio_channels = 1
        mock_settings.return_value.audio_chunk_size = 1024
        
        from jarvis.audio.playback import AudioPlayback
        playback = AudioPlayback(audio_queue=mock_audio_queue)
        
        with patch('sounddevice.RawOutputStream') as mock_stream:
            mock_stream_instance = Mock()
            mock_stream.return_value = mock_stream_instance
            
            # Multiple start/stop cycles
            for i in range(3):
                playback.start()
                assert playback._running
                playback.stop()
                assert not playback._running


def test_audio_playback_custom_settings():
    """Test audio playback with custom settings."""
    mock_audio_queue = Mock()
    mock_audio_queue.get_nowait.side_effect = Exception("Queue empty")
    
    # Create custom settings
    custom_settings = Mock()
    custom_settings.audio_receive_sample_rate = 44100
    custom_settings.audio_channels = 1
    custom_settings.audio_chunk_size = 512
    
    from jarvis.audio.playback import AudioPlayback
    playback = AudioPlayback(audio_queue=mock_audio_queue, settings=custom_settings)
    
    assert playback.settings == custom_settings
    assert playback.settings.audio_receive_sample_rate == 44100


def test_audio_playback_callback_oversized_data():
    """Test audio playback callback with oversized audio data."""
    mock_audio_queue = Mock()
    
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_receive_sample_rate = 24000
        mock_settings.return_value.audio_channels = 1
        mock_settings.return_value.audio_chunk_size = 1024
        
        from jarvis.audio.playback import AudioPlayback
        playback = AudioPlayback(audio_queue=mock_audio_queue)
        
        # Test with oversized data
        playback._running = True
        test_data = b"\x01\x02" * 2048  # 4096 bytes = 2048 frames * 2 bytes
        mock_audio_queue.get_nowait.return_value = test_data
        
        outdata = np.zeros((1024, 1), dtype=np.int16)
        playback._AudioPlayback__callback(outdata, 1024, {}, None)
        
        # Should only use first part of data
        assert not np.all(outdata == 0)


def test_audio_playback_cleanup():
    """Test proper cleanup of audio resources."""
    mock_audio_queue = Mock()
    mock_audio_queue.get_nowait.side_effect = Exception("Queue empty")
    
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_receive_sample_rate = 24000
        mock_settings.return_value.audio_channels = 1
        mock_settings.return_value.audio_chunk_size = 1024
        
        from jarvis.audio.playback import AudioPlayback
        playback = AudioPlayback(audio_queue=mock_audio_queue)
        
        with patch('sounddevice.RawOutputStream') as mock_stream:
            mock_stream_instance = Mock()
            mock_stream.return_value = mock_stream_instance
            
            # Start playback
            playback.start()
            
            # Cleanup
            playback.stop()
            
            assert not playback._running
            mock_stream_instance.stop.assert_called_once()


def test_audio_playback_stereo_channels():
    """Test audio playback with stereo channels."""
    mock_audio_queue = Mock()
    mock_audio_queue.get_nowait.side_effect = Exception("Queue empty")
    
    with patch('jarvis.audio.playback.get_settings') as mock_settings:
        mock_settings.return_value.audio_receive_sample_rate = 24000
        mock_settings.return_value.audio_channels = 2
        mock_settings.return_value.audio_chunk_size = 1024
        
        from jarvis.audio.playback import AudioPlayback
        playback = AudioPlayback(audio_queue=mock_audio_queue)
        
        with patch('sounddevice.RawOutputStream') as mock_stream:
            mock_stream_instance = Mock()
            mock_stream.return_value = mock_stream_instance
            
            playback.start()
            
            # Verify stream was called with stereo channels
            call_args = mock_stream.call_args
            assert call_args[1]['channels'] == 2
            
            playback.stop()


def test_audio_playback_different_sample_rates():
    """Test audio playback with different sample rates."""
    mock_audio_queue = Mock()
    mock_audio_queue.get_nowait.side_effect = Exception("Queue empty")
    
    sample_rates = [8000, 16000, 22050, 44100, 48000]
    
    for sample_rate in sample_rates:
        with patch('jarvis.audio.playback.get_settings') as mock_settings:
            mock_settings.return_value.audio_receive_sample_rate = sample_rate
            mock_settings.return_value.audio_channels = 1
            mock_settings.return_value.audio_chunk_size = 1024
            
            from jarvis.audio.playback import AudioPlayback
            playback = AudioPlayback(audio_queue=mock_audio_queue)
            
            with patch('sounddevice.RawOutputStream') as mock_stream:
                mock_stream_instance = Mock()
                mock_stream.return_value = mock_stream_instance
                
                playback.start()
                
                # Verify sample rate
                call_args = mock_stream.call_args
                assert call_args[1]['samplerate'] == sample_rate
                
                playback.stop()
