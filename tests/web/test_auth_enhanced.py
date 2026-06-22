"""Enhanced authentication tests for comprehensive coverage (>70%)."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock
import time
from typing import Any


def test_auth_manager_initialization():
    """Test AuthManager initialization with default values."""
    from jarvis.web.auth import AuthManager
    from jarvis.config.settings import Settings
    
    settings = Settings()
    auth = AuthManager(settings)
    
    assert auth.settings == settings
    assert auth._pending_pins == {}
    assert auth._tokens == set()
    assert auth._token_keys == {}
    assert auth._aes_cache == {}
    assert auth._device_sessions == {}
    assert auth._failed_attempts == {}
    assert auth._max_attempts == 5
    assert auth._lockout_seconds == 60


def test_auth_is_locked_out_new_ip():
    """Test lockout status for new IP addresses."""
    from jarvis.web.auth import AuthManager
    from jarvis.config.settings import Settings
    
    auth = AuthManager(Settings())
    
    # New IP should not be locked out
    assert auth.is_locked_out("192.168.1.1") is False
    assert auth.is_locked_out("127.0.0.1") is False
    assert auth.is_locked_out("10.0.0.1") is False


def test_auth_record_attempt_success():
    """Test recording successful login attempts."""
    from jarvis.web.auth import AuthManager
    from jarvis.config.settings import Settings
    
    auth = AuthManager(Settings())
    
    # Record successful attempt
    auth.record_attempt("192.168.1.1", success=True)
    
    # Should not be locked out and no failed attempts recorded
    assert auth.is_locked_out("192.168.1.1") is False
    assert "192.168.1.1" not in auth._failed_attempts


def test_auth_record_attempt_failure_single():
    """Test recording single failed login attempt."""
    from jarvis.web.auth import AuthManager
    from jarvis.config.settings import Settings
    
    auth = AuthManager(Settings())
    
    # Record failed attempt
    auth.record_attempt("192.168.1.1", success=False)
    
    # Should not be locked out yet
    assert auth.is_locked_out("192.168.1.1") is False
    assert "192.168.1.1" in auth._failed_attempts
    assert auth._failed_attempts["192.168.1.1"] == (1, 0.0)


def test_auth_record_attempt_multiple_failures():
    """Test recording multiple failed login attempts."""
    from jarvis.web.auth import AuthManager
    from jarvis.config.settings import Settings
    
    auth = AuthManager(Settings())
    
    # Record 4 failed attempts (below threshold)
    for i in range(4):
        auth.record_attempt("192.168.1.1", success=False)
        assert auth.is_locked_out("192.168.1.1") is False
    
    # 5th failed attempt should trigger lockout
    auth.record_attempt("192.168.1.1", success=False)
    assert auth.is_locked_out("192.168.1.1") is True
    assert auth._failed_attempts["192.168.1.1"][0] == 5


def test_auth_lockout_expiration():
    """Test that lockout expires after timeout period."""
    from jarvis.web.auth import AuthManager
    from jarvis.config.settings import Settings
    
    auth = AuthManager(Settings())
    auth._lockout_seconds = 1  # Short timeout for testing
    
    # Trigger lockout
    for i in range(5):
        auth.record_attempt("192.168.1.1", success=False)
    assert auth.is_locked_out("192.168.1.1") is True
    
    # Wait for lockout to expire
    time.sleep(1.1)
    assert auth.is_locked_out("192.168.1.1") is False


def test_auth_new_pin_creation():
    """Test PIN creation with default expiry."""
    from jarvis.web.auth import AuthManager
    from jarvis.config.settings import Settings
    
    auth = AuthManager(Settings())
    
    # Create PIN
    pin = auth.new_pin()
    
    assert isinstance(pin, str)
    assert len(pin) == 6  # Default PIN length
    assert pin.isdigit()
    assert pin in auth._pending_pins
    assert auth._pending_pins[pin] > time.time()


def test_auth_new_pin_custom_expiry():
    """Test PIN creation with custom expiry time."""
    from jarvis.web.auth import AuthManager
    from jarvis.config.settings import Settings
    
    auth = AuthManager(Settings())
    
    # Create PIN with custom expiry
    pin = auth.new_pin(expiry_secs=3600)
    expiry_time = auth._pending_pins[pin]
    
    assert isinstance(pin, str)
    assert len(pin) == 6
    assert expiry_time > time.time()
    assert expiry_time < time.time() + 3700  # Allow some margin


def test_auth_new_pin_cleanup_expired():
    """Test that expired PINs are cleaned up when creating new PINs."""
    from jarvis.web.auth import AuthManager
    from jarvis.config.settings import Settings
    
    auth = AuthManager(Settings())
    
    # Create PIN with very short expiry
    old_pin = auth.new_pin(expiry_secs=1)
    assert old_pin in auth._pending_pins
    
    # Wait for expiry
    time.sleep(1.1)
    
    # Create new PIN (should trigger cleanup)
    new_pin = auth.new_pin()
    assert old_pin not in auth._pending_pins
    assert new_pin in auth._pending_pins


def test_auth_validate_pin_success():
    """Test successful PIN validation."""
    from jarvis.web.auth import AuthManager
    from jarvis.config.settings import Settings
    
    auth = AuthManager(Settings())
    
    # Create and validate PIN
    pin = auth.new_pin()
    session_key = auth.validate_pin(pin, "192.168.1.1")
    
    assert isinstance(session_key, str)
    assert len(session_key) == 32  # Session key length
    assert pin not in auth._pending_pins  # PIN should be consumed
    assert auth.is_locked_out("192.168.1.1") is False


def test_auth_validate_pin_invalid():
    """Test PIN validation with invalid PIN."""
    from jarvis.web.auth import AuthManager
    from jarvis.config.settings import Settings
    
    auth = AuthManager(Settings())
    
    # Try to validate non-existent PIN
    session_key = auth.validate_pin("123456", "192.168.1.1")
    assert session_key is None
    
    # Should record failed attempt
    assert auth.is_locked_out("192.168.1.1") is False
    assert "192.168.1.1" in auth._failed_attempts


def test_auth_validate_pin_expired():
    """Test PIN validation with expired PIN."""
    from jarvis.web.auth import AuthManager
    from jarvis.config.settings import Settings
    
    auth = AuthManager(Settings())
    
    # Create PIN with short expiry
    pin = auth.new_pin(expiry_secs=1)
    time.sleep(1.1)  # Wait for expiry
    
    # Try to validate expired PIN
    session_key = auth.validate_pin(pin, "192.168.1.1")
    assert session_key is None


def test_auth_validate_pin_locked_out():
    """Test PIN validation when IP is locked out."""
    from jarvis.web.auth import AuthManager
    from jarvis.config.settings import Settings
    
    auth = AuthManager(Settings())
    
    # Trigger lockout
    for i in range(5):
        auth.record_attempt("192.168.1.1", success=False)
    assert auth.is_locked_out("192.168.1.1") is True
    
    # Try to validate PIN while locked out
    pin = auth.new_pin()
    session_key = auth.validate_pin(pin, "192.168.1.1")
    assert session_key is None


def test_auth_create_token():
    """Test bearer token creation."""
    from jarvis.web.auth import AuthManager
    from jarvis.config.settings import Settings
    
    auth = AuthManager(Settings())
    
    # Create token
    session_key = "test_session_key_123"
    token = auth.create_token(session_key)
    
    assert isinstance(token, str)
    assert len(token) > 0
    assert token in auth._tokens
    assert auth._token_keys[token] == session_key
    assert session_key in auth._aes_cache


def test_auth_is_valid_token():
    """Test token validation."""
    from jarvis.web.auth import AuthManager
    from jarvis.config.settings import Settings
    
    auth = AuthManager(Settings())
    
    # Test invalid token
    assert auth.is_valid_token("invalid_token") is False
    
    # Create and test valid token
    session_key = "test_session_key"
    token = auth.create_token(session_key)
    assert auth.is_valid_token(token) is True


def test_auth_get_aes_key():
    """Test AES key retrieval."""
    from jarvis.web.auth import AuthManager
    from jarvis.config.settings import Settings
    
    auth = AuthManager(Settings())
    
    # Test invalid token
    assert auth.get_aes_key("invalid_token") is None
    
    # Create and test valid token
    session_key = "test_session_key"
    token = auth.create_token(session_key)
    aes_key = auth.get_aes_key(token)
    
    assert aes_key is not None
    assert isinstance(aes_key, bytes)
    assert len(aes_key) == 32  # AES-256 key length


def test_auth_create_device_session():
    """Test device session creation."""
    from jarvis.web.auth import AuthManager
    from jarvis.config.settings import Settings
    
    auth = AuthManager(Settings())
    
    # Create device session
    session_key = "test_session_key"
    device_token = auth.create_device_session(session_key)
    
    assert isinstance(device_token, str)
    assert len(device_token) > 0
    assert device_token in auth._device_sessions
    assert auth._device_sessions[device_token]["session_key"] == session_key


def test_auth_validate_device_token():
    """Test device token validation."""
    from jarvis.web.auth import AuthManager
    from jarvis.config.settings import Settings
    
    auth = AuthManager(Settings())
    
    # Test invalid device token
    assert auth.validate_device_token("invalid_device_token") is None
    
    # Create and test valid device token
    session_key = "test_session_key"
    device_token = auth.create_device_session(session_key)
    returned_session_key = auth.validate_device_token(device_token)
    
    assert returned_session_key == session_key


def test_auth_revoke_devices():
    """Test revoking all device sessions."""
    from jarvis.web.auth import AuthManager
    from jarvis.config.settings import Settings
    
    auth = AuthManager(Settings())
    
    # Create multiple device sessions
    for i in range(3):
        auth.create_device_session(f"session_key_{i}")
    
    # Revoke all devices
    revoked_count = auth.revoke_devices()
    assert revoked_count == 3
    assert len(auth._device_sessions) == 0


def test_auth_revoke_token():
    """Test revoking a single token."""
    from jarvis.web.auth import AuthManager
    from jarvis.config.settings import Settings
    
    auth = AuthManager(Settings())
    
    # Create token
    session_key = "test_session_key"
    token = auth.create_token(session_key)
    
    # Verify token exists
    assert auth.is_valid_token(token) is True
    assert auth.get_aes_key(token) is not None
    
    # Revoke token
    auth.revoke_token(token)
    
    # Verify token is revoked
    assert auth.is_valid_token(token) is False
    assert auth.get_aes_key(token) is None


def test_auth_get_token_from_header():
    """Test extracting token from request headers."""
    from jarvis.web.auth import AuthManager
    from jarvis.config.settings import Settings
    
    auth = AuthManager(Settings())
    
    # Mock request with Bearer token
    request = Mock()
    request.headers = {"authorization": "Bearer test_token_123"}
    
    token = auth.get_token_from_header(request)
    assert token == "test_token_123"
    
    # Mock request without authorization
    request.headers = {}
    token = auth.get_token_from_header(request)
    assert token == ""
    
    # Mock request with malformed header
    request.headers = {"authorization": "test_token_123"}
    token = auth.get_token_from_header(request)
    assert token == "test_token_123"


def test_auth_concurrent_pin_validation():
    """Test concurrent PIN validation."""
    import threading
    from jarvis.web.auth import AuthManager
    from jarvis.config.settings import Settings
    
    auth = AuthManager(Settings())
    results = []
    
    def validate_pin_worker():
        pin = auth.new_pin()
        session_key = auth.validate_pin(pin, "127.0.0.1")
        results.append(session_key is not None)
    
    # Create multiple threads
    threads = []
    for i in range(5):
        thread = threading.Thread(target=validate_pin_worker)
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # All validations should succeed
    assert all(results)
    assert len(results) == 5


def test_auth_multiple_ips_independent():
    """Test that different IPs are tracked independently."""
    from jarvis.web.auth import AuthManager
    from jarvis.config.settings import Settings
    
    auth = AuthManager(Settings())
    ips = ["192.168.1.1", "192.168.1.2", "10.0.0.1"]
    
    # Trigger lockout for first IP
    for i in range(5):
        auth.record_attempt(ips[0], success=False)
    
    # Only first IP should be locked out
    assert auth.is_locked_out(ips[0]) is True
    assert auth.is_locked_out(ips[1]) is False
    assert auth.is_locked_out(ips[2]) is False


def test_auth_session_persistence():
    """Test that sessions persist across multiple operations."""
    from jarvis.web.auth import AuthManager
    from jarvis.config.settings import Settings
    
    auth = AuthManager(Settings())
    
    # Create PIN and validate
    pin = auth.new_pin()
    session_key = auth.validate_pin(pin, "192.168.1.1")
    
    # Create token from session
    token = auth.create_token(session_key)
    
    # Verify all components are linked
    assert auth.is_valid_token(token) is True
    assert auth.get_aes_key(token) is not None
    assert auth._token_keys[token] == session_key
    
    # Create device session
    device_token = auth.create_device_session(session_key)
    assert auth.validate_device_token(device_token) == session_key


def test_auth_edge_cases():
    """Test edge cases and boundary conditions."""
    from jarvis.web.auth import AuthManager
    from jarvis.config.settings import Settings
    
    auth = AuthManager(Settings())
    
    # Test with empty strings
    assert auth.is_locked_out("") is False
    assert auth.validate_pin("", "127.0.0.1") is None
    
    # Test with very long strings
    long_ip = "192.168.1." + "1" * 100
    assert auth.is_locked_out(long_ip) is False
    
    # Test rapid successive attempts
    for i in range(10):
        auth.record_attempt("rapid_ip", success=False)
    assert auth.is_locked_out("rapid_ip") is True


def test_auth_error_handling():
    """Test error handling in authentication methods."""
    from jarvis.web.auth import AuthManager
    from jarvis.config.settings import Settings
    
    auth = AuthManager(Settings())
    
    # Test with None inputs (should not crash)
    try:
        auth.record_attempt(None, success=False)  # type: ignore
        auth.is_locked_out(None)  # type: ignore
    except (TypeError, AttributeError):
        pass  # Expected for invalid inputs
    
    # Test revoke operations on non-existent items
    auth.revoke_token("non_existent_token")  # Should not crash
    revoked_count = auth.revoke_devices()  # Should return 0
    assert revoked_count == 0
