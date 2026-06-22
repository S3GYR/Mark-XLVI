"""Tests for dashboard crypto helpers."""

from __future__ import annotations

from jarvis.web.crypto import decrypt_aes, derive_key, encrypt_aes


def test_derive_key_is_stable():
    """The same session key always produces the same AES key."""
    key = derive_key("session-abc")
    assert key == derive_key("session-abc")
    assert key != derive_key("session-def")
    assert len(key) == 32


def test_encrypt_decrypt_roundtrip():
    """Encrypting and decrypting returns the original plaintext."""
    key = derive_key("session-abc")
    plaintext = "Hello, JARVIS!"
    encrypted = encrypt_aes(plaintext, key)
    decrypted = decrypt_aes(encrypted, key)
    assert decrypted == plaintext


def test_decrypt_with_wrong_key_fails():
    """Decrypting with the wrong key returns None."""
    key1 = derive_key("session-abc")
    key2 = derive_key("session-def")
    encrypted = encrypt_aes("secret", key1)
    assert decrypt_aes(encrypted, key2) is None
