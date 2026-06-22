"""Authentication and session management for the dashboard."""

from __future__ import annotations

import time
from typing import Any

from jarvis.config.settings import Settings
from jarvis.web.crypto import derive_key, generate_pin, generate_token


class AuthManager:
    """Manages PINs, bearer tokens, and device sessions for the dashboard."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._pending_pins: dict[str, float] = {}
        self._tokens: set[str] = set()
        self._token_keys: dict[str, str] = {}  # token -> session_key
        self._aes_cache: dict[str, bytes] = {}  # session_key -> AES key
        self._device_sessions: dict[str, dict] = {}  # device_token -> metadata
        self._failed_attempts: dict[str, tuple[int, float]] = {}  # ip -> (count, lockout_until)
        self._max_attempts = 5
        self._lockout_seconds = 60

    def is_locked_out(self, ip: str) -> bool:
        """Return True if the IP is currently locked out."""
        if ip not in self._failed_attempts:
            return False
        count, lockout_until = self._failed_attempts[ip]
        return count >= self._max_attempts and time.time() < lockout_until

    def record_attempt(self, ip: str, success: bool) -> None:
        """Record a login attempt for rate limiting."""
        now = time.time()
        if success:
            self._failed_attempts.pop(ip, None)
            return

        count, lockout_until = self._failed_attempts.get(ip, (0, 0.0))
        if lockout_until and now > lockout_until:
            count = 0
        count += 1
        lockout_until = now + self._lockout_seconds if count >= self._max_attempts else 0.0
        self._failed_attempts[ip] = (count, lockout_until)

    def new_pin(self, expiry_secs: int = 600) -> str:
        """Create a new one-time PIN."""
        now = time.time()
        self._pending_pins = {k: v for k, v in self._pending_pins.items() if v > now}
        pin = generate_pin()
        self._pending_pins[pin] = now + expiry_secs
        return pin

    def validate_pin(self, pin: str, ip: str) -> str | None:
        """Validate a PIN and return a session key if valid."""
        if self.is_locked_out(ip):
            return None
        now = time.time()
        if pin in self._pending_pins and self._pending_pins[pin] > now:
            del self._pending_pins[pin]
            self.record_attempt(ip, True)
            return generate_pin(32)  # session key
        self.record_attempt(ip, False)
        return None

    def create_token(self, session_key: str) -> str:
        """Create a bearer token bound to a session key."""
        token = generate_token()
        self._tokens.add(token)
        self._token_keys[token] = session_key
        self._aes_cache[session_key] = derive_key(session_key)
        return token

    def is_valid_token(self, token: str) -> bool:
        """Return True if the token is active."""
        return token in self._tokens

    def get_aes_key(self, token: str) -> bytes | None:
        """Return the AES key for a token."""
        session_key = self._token_keys.get(token)
        if not session_key:
            return None
        return self._aes_cache.get(session_key)

    def create_device_session(self, session_key: str) -> str:
        """Create a persistent device token for a session key."""
        device_token = generate_token()
        self._device_sessions[device_token] = {"session_key": session_key}
        return device_token

    def validate_device_token(self, device_token: str) -> str | None:
        """Return the session key for a known device token."""
        session = self._device_sessions.get(device_token)
        if not session:
            return None
        return session.get("session_key")

    def revoke_devices(self) -> int:
        """Revoke all device sessions."""
        count = len(self._device_sessions)
        self._device_sessions.clear()
        return count

    def revoke_token(self, token: str) -> None:
        """Revoke a single token."""
        self._tokens.discard(token)
        self._token_keys.pop(token, None)

    def get_token_from_header(self, request: Any) -> str:
        """Extract the bearer token from request headers."""
        auth = request.headers.get("authorization", "")
        return auth.removeprefix("Bearer ").strip()
