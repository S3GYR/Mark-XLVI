"""Fixed tests for Phone Audio Relay components."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
from typing import Any


def test_phone_audio_relay_initialization():
    """Test phone audio relay initialization with proper configuration."""
    mock_callback = Mock()
    
    from jarvis.audio.phone_relay import PhoneAudioRelay
    relay = PhoneAudioRelay(mock_callback, max_queue_size=100)
    
    assert relay is not None
    assert relay.output_callback == mock_callback
    assert relay.queue.maxsize == 100
    assert not relay._running
    assert relay._task is None


def test_phone_audio_relay_start_stop():
    """Test phone audio relay start and stop functionality."""
    mock_callback = Mock()
    
    from jarvis.audio.phone_relay import PhoneAudioRelay
    relay = PhoneAudioRelay(mock_callback)
    
    async def test_start_stop():
        # Start the relay
        await relay.start()
        assert relay._running
        assert relay._task is not None
        
        # Stop the relay
        await relay.stop()
        assert not relay._running
        assert relay._task is None
    
    asyncio.run(test_start_stop())


def test_phone_audio_relay_audio_forwarding():
    """Test audio forwarding through the relay."""
    mock_callback = Mock()
    
    from jarvis.audio.phone_relay import PhoneAudioRelay
    relay = PhoneAudioRelay(mock_callback)
    
    async def test_forwarding():
        await relay.start()
        
        # Put audio data
        test_audio = b"test_audio_data"
        await relay.put(test_audio)
        
        # Give time for forwarding
        await asyncio.sleep(0.01)
        
        # Check callback was called
        mock_callback.assert_called_with({"data": test_audio, "mime_type": "audio/pcm"})
        
        await relay.stop()
    
    asyncio.run(test_forwarding())


def test_phone_audio_relay_queue_full_handling():
    """Test handling of full queue."""
    mock_callback = Mock()
    
    from jarvis.audio.phone_relay import PhoneAudioRelay
    relay = PhoneAudioRelay(mock_callback, max_queue_size=1)
    
    async def test_queue_full():
        await relay.start()
        
        # Fill the queue
        await relay.put(b"audio1")
        
        # Try to add more (should handle gracefully)
        await relay.put(b"audio2")
        
        await relay.stop()
    
    asyncio.run(test_queue_full())


def test_phone_audio_relay_error_handling():
    """Test error handling in audio forwarding."""
    mock_callback = Mock()
    mock_callback.side_effect = Exception("Callback error")
    
    from jarvis.audio.phone_relay import PhoneAudioRelay
    relay = PhoneAudioRelay(mock_callback)
    
    async def test_error_handling():
        await relay.start()
        
        # Put audio data (should handle callback error)
        await relay.put(b"error_audio")
        
        # Give time for error handling
        await asyncio.sleep(0.01)
        
        await relay.stop()
    
    asyncio.run(test_error_handling())


def test_phone_audio_relay_concurrent_operations():
    """Test concurrent put operations."""
    mock_callback = Mock()
    
    from jarvis.audio.phone_relay import PhoneAudioRelay
    relay = PhoneAudioRelay(mock_callback)
    
    async def test_concurrent():
        await relay.start()
        
        # Put multiple audio chunks concurrently
        tasks = []
        for i in range(5):
            task = asyncio.create_task(relay.put(f"audio_{i}".encode()))
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        # Give time for processing
        await asyncio.sleep(0.01)
        
        await relay.stop()
    
    asyncio.run(test_concurrent())


def test_phone_audio_relay_stop_cancellation():
    """Test that stop properly cancels the forwarding task."""
    mock_callback = Mock()
    
    from jarvis.audio.phone_relay import PhoneAudioRelay
    relay = PhoneAudioRelay(mock_callback)
    
    async def test_stop_cancellation():
        await relay.start()
        assert relay._task is not None
        
        # Stop should cancel the task
        await relay.stop()
        assert relay._task is None
        assert not relay._running
    
    asyncio.run(test_stop_cancellation())


def test_phone_audio_relay_data_format():
    """Test that audio data is properly formatted."""
    mock_callback = Mock()
    
    from jarvis.audio.phone_relay import PhoneAudioRelay
    relay = PhoneAudioRelay(mock_callback)
    
    async def test_data_format():
        await relay.start()
        
        test_audio = b"pcm_audio_data"
        await relay.put(test_audio)
        
        await asyncio.sleep(0.01)
        
        # Verify the data format
        expected_format = {"data": test_audio, "mime_type": "audio/pcm"}
        mock_callback.assert_called_with(expected_format)
        
        await relay.stop()
    
    asyncio.run(test_data_format())


def test_phone_audio_relay_multiple_starts():
    """Test handling multiple start calls."""
    mock_callback = Mock()
    
    from jarvis.audio.phone_relay import PhoneAudioRelay
    relay = PhoneAudioRelay(mock_callback)
    
    async def test_multiple_starts():
        # Start multiple times
        await relay.start()
        await relay.start()
        await relay.start()
        
        assert relay._running
        
        await relay.stop()
    
    asyncio.run(test_multiple_starts())


def test_phone_audio_relay_multiple_stops():
    """Test handling multiple stop calls."""
    mock_callback = Mock()
    
    from jarvis.audio.phone_relay import PhoneAudioRelay
    relay = PhoneAudioRelay(mock_callback)
    
    async def test_multiple_stops():
        await relay.start()
        
        # Stop multiple times
        await relay.stop()
        await relay.stop()
        await relay.stop()
        
        assert not relay._running
        assert relay._task is None
    
    asyncio.run(test_multiple_stops())


def test_phone_audio_relay_empty_queue():
    """Test behavior with empty queue."""
    mock_callback = Mock()
    
    from jarvis.audio.phone_relay import PhoneAudioRelay
    relay = PhoneAudioRelay(mock_callback)
    
    async def test_empty_queue():
        await relay.start()
        
        # Don't put any data, just let it run briefly
        await asyncio.sleep(0.01)
        
        await relay.stop()
    
    asyncio.run(test_empty_queue())


def test_phone_audio_relay_large_audio_data():
    """Test handling of large audio data chunks."""
    mock_callback = Mock()
    
    from jarvis.audio.phone_relay import PhoneAudioRelay
    relay = PhoneAudioRelay(mock_callback)
    
    async def test_large_data():
        await relay.start()
        
        # Large audio chunk
        large_audio = b"x" * 10000
        await relay.put(large_audio)
        
        await asyncio.sleep(0.01)
        
        mock_callback.assert_called_with({"data": large_audio, "mime_type": "audio/pcm"})
        
        await relay.stop()
    
    asyncio.run(test_large_data())


def test_phone_audio_relay_callback_exception():
    """Test that callback exceptions don't crash the relay."""
    mock_callback = Mock()
    call_count = 0
    
    def side_effect(data):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("First call fails")
    
    mock_callback.side_effect = side_effect
    
    from jarvis.audio.phone_relay import PhoneAudioRelay
    relay = PhoneAudioRelay(mock_callback)
    
    async def test_callback_exception():
        await relay.start()
        
        # Put multiple audio chunks
        await relay.put(b"audio1")
        await relay.put(b"audio2")
        
        await asyncio.sleep(0.01)
        
        # Both should have been attempted despite the first failure
        assert call_count == 2
        
        await relay.stop()
    
    asyncio.run(test_callback_exception())
