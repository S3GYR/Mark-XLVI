"""Cryptographic helpers for the dashboard."""

from __future__ import annotations

import base64
import hashlib
import secrets

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from jarvis.config.paths import CONFIG_DIR

_AES_SALT = b"JARVIS-DASHBOARD-v2"


def derive_key(session_key: str) -> bytes:
    """Derive a 32-byte AES key from a session key using SHA-256.

    This is intentionally fast for real-time chat; the session key is a
    high-entropy random token delivered out-of-band via QR code.
    """
    return hashlib.sha256(session_key.encode("utf-8") + _AES_SALT).digest()


def encrypt_aes(plaintext: str, key: bytes) -> str:
    """Encrypt plaintext with AES-256-GCM and return base64(nonce ‖ ciphertext ‖ tag)."""
    nonce = secrets.token_bytes(12)
    cipher = Cipher(algorithms.AES(key), modes.GCM(nonce))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext.encode("utf-8")) + encryptor.finalize()
    return base64.b64encode(nonce + ciphertext + encryptor.tag).decode("ascii")


def decrypt_aes(ciphertext_b64: str, key: bytes) -> str | None:
    """Decrypt base64(nonce ‖ ciphertext ‖ tag) with AES-256-GCM."""
    try:
        raw = base64.b64decode(ciphertext_b64)
        nonce, ciphertext, tag = raw[:12], raw[12:-16], raw[-16:]
        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag))
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        return plaintext.decode("utf-8")
    except Exception:
        return None


def generate_pin(length: int = 6) -> str:
    """Generate a numeric PIN avoiding ambiguous characters."""
    return "".join(secrets.choice("23456789") for _ in range(length))


def generate_token() -> str:
    """Generate a URL-safe bearer token."""
    return secrets.token_urlsafe(32)
