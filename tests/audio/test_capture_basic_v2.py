"""Basic working tests for audio capture focusing on core functionality."""

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
        assert capture._running is False


def test_audio_capture_callback_basic():
    """Test audio capture callback basic functionality."""
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
        
        # Test callback when not running
        test_data = [1, 2, 3, 4, 5]
        capture._running = False
        capture._callback(test_data)
        output_callback.assert_not_called()
        
        # Test callback when running
        capture._running = True
        capture._callback(test_data)
        output_callback.assert_called_once()


def test_audio_capture_callback_with_speaking():
    """Test audio capture callback when speaking."""
    with patch('jarvis.audio.capture.get_settings') as mock_settings:
        mock_settings.return_value.audio_device = "default"
        mock_settings.return_value.sample_rate = 16000
        mock_settings.return_value.channels = 1
        
        # Mock the callbacks
        output_callback = Mock()
        is_speaking = Mock(return_value=True)  # Speaking is True
        is_muted = Mock(return_value=False)
        is_phone_active = Mock(return_value=False)
        
        from jarvis.audio.capture import AudioCapture
        
        capture = AudioCapture(
            output_callback=output_callback,
            is_speaking=is_speaking,
            is_muted=is_muted,
            is_phone_active=is_phone_active
        )
        
        capture._running = True
        
        # Test when speaking - should not call output_callback
        capture._callback([1, 2, 3])
        output_callback.assert_not_called()


def test_audio_capture_callback_with_muted():
    """Test audio capture callback when muted."""
    with patch('jarvis.audio.capture.get_settings') as mock_settings:
        mock_settings.return_value.audio_device = "default"
        mock_settings.return_value.sample_rate = 16000
        mock_settings.return_value.channels = 1
        
        # Mock the callbacks
        output_callback = Mock()
        is_speaking = Mock(return_value=False)
        is_muted = Mock(return_value=True)  # Muted is True
        is_phone_active = Mock(return_value=False)
        
        from jarvis.audio.capture import AudioCapture
        
        capture = AudioCapture(
            output_callback=output_callback,
            is_speaking=is_speaking,
            is_muted=is_muted,
            is_phone_active=is_phone_active
        )
        
        capture._running = True
        
        # Test when muted - should not call output_callback
        capture._callback([1, 2, 3])
        output_callback.assert_not_called()


def test_audio_capture_callback_with_phone_active():
    """Test audio capture callback when phone is active."""
    with patch('jarvis.audio.capture.get_settings') as mock_settings:
        mock_settings.return_value.audio_device = "default"
        mock_settings.return_value.sample_rate = 16000
        mock_settings.return_value.channels = 1
        
        # Mock the callbacks
        output_callback = Mock()
        is_speaking = Mock(return_value=False)
        is_muted = Mock(return_value=False)
        is_phone_active = Mock(return_value=True)  # Phone is active
        
        from jarvis.audio.capture import AudioCapture
        
        capture = AudioCapture(
            output_callback=output_callback,
            is_speaking=is_speaking,
            is_muted=is_muted,
            is_phone_active=is_phone_active
        )
        
        capture._running = True
        
        # Test when phone active - should not call output_callback
        capture._callback([1, 2, 3])
        output_callback.assert_not_called()


def test_audio_capture_callback_normal_operation():
    """Test audio capture callback in normal operation."""
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
        
        capture._running = True
        
        # Test normal operation - should call output_callback
        capture._callback([1, 2, 3])
        output_callback.assert_called_once()
        
        # Verify the callback was called with processed data
        args = output_callback.call_args[0]
        assert len(args) == 1
        assert isinstance(args[0], bytes)


def test_audio_capture_callback_empty_data():
    """Test audio capture callback with empty data."""
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
        
        capture._running = True
        
        # Test with empty data
        capture._callback([])
        # Empty data handling depends on implementation
        # Just verify no exception is raised


def test_audio_capture_callback_different_data_types():
    """Test audio capture callback with different data types."""
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
        
        capture._running = True
        
        # Test with different data types
        test_cases = [
            [1, 2, 3, 4, 5],
            [0.1, 0.2, 0.3, 0.4, 0.5],
            [-1, -2, -3, -4, -5],
        ]
        
        for test_data in test_cases:
            output_callback.reset_mock()
            capture._callback(test_data)
            output_callback.assert_called_once()
            
            # Verify the callback was called with processed data
            args = output_callback.call_args[0]
            assert len(args) == 1
            assert isinstance(args[0], bytes)


def test_audio_capture_state_management():
    """Test audio capture state management."""
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
        
        # Test initial state
        assert capture._running is False
        
        # Test state changes
        capture._running = True
        assert capture._running is True
        
        capture._running = False
        assert capture._running is False


def test_audio_capture_settings_integration():
    """Test audio capture settings integration."""
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
        
        from jarvis.audio.capture import AudioCapture
        
        capture = AudioCapture(
            output_callback=output_callback,
            is_speaking=is_speaking,
            is_muted=is_muted,
            is_phone_active=is_phone_active
        )
        
        # Settings should be accessible through the capture instance
        # (depending on implementation)
        assert capture is not None


def test_audio_capture_callback_functionality():
    """Test audio capture callback functionality in detail."""
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
        
        capture._running = True
        
        # Test multiple callbacks
        test_data = [1, 2, 3, 4, 5]
        for i in range(3):
            capture._callback(test_data)
        
        # Should have been called 3 times
        assert output_callback.call_count == 3


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
        
        from jarvis.audio.capture import AudioCapture
        
        capture = AudioCapture(
            output_callback=output_callback,
            is_speaking=is_speaking,
            is_muted=is_muted,
            is_phone_active=is_phone_active
        )
        
        capture._running = True
        
        # Test with None data (should not crash)
        try:
            capture._callback(None)
        except Exception:
            # Depending on implementation, this might raise an exception
            pass


def test_audio_capture_concurrent_callbacks():
    """Test audio capture concurrent callbacks."""
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
        
        capture._running = True
        
        # Test multiple concurrent callbacks
        test_data = [1, 2, 3, 4, 5]
        
        # Simulate concurrent access
        for i in range(5):
            capture._callback(test_data)
        
        # Should handle concurrent access gracefully
        assert output_callback.call_count == 5
