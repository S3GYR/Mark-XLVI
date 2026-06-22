"""Secure secret management for API keys and credentials."""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any

import keyring
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from jarvis.config.paths import CONFIG_DIR

SERVICE_NAME = "jarvis"
KEYRING_USERNAME = "api_keys"


def _derive_key(password: str, salt: bytes) -> bytes:
    """Derive a Fernet key from a password and salt."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def _get_machine_salt() -> bytes:
    """Return a stable per-machine salt stored in the config directory."""
    salt_file = CONFIG_DIR / ".salt"
    if salt_file.exists():
        return salt_file.read_bytes()
    salt = os.urandom(16)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    salt_file.write_bytes(salt)
    return salt


def get_secret(name: str, env_override: str | None = None) -> str | None:
    """Get a secret from environment, keyring, or encrypted file."""
    # 1. Environment variable override
    env_name = env_override or name.upper()
    value = os.getenv(env_name)
    if value:
        return value

    # 2. Keyring
    try:
        value = keyring.get_password(SERVICE_NAME, name)
        if value:
            return value
    except Exception:
        pass

    # 3. Encrypted fallback file
    secrets_file = CONFIG_DIR / "secrets.enc"
    if secrets_file.exists():
        return _load_from_encrypted_file(secrets_file, name)

    return None


def set_secret(name: str, value: str) -> None:
    """Store a secret securely using keyring or encrypted file fallback."""
    try:
        keyring.set_password(SERVICE_NAME, name, value)
        return
    except Exception:
        pass

    # Fallback to encrypted file
    secrets_file = CONFIG_DIR / "secrets.enc"
    secrets = _load_all_encrypted(secrets_file) if secrets_file.exists() else {}
    secrets[name] = value
    _save_encrypted_file(secrets_file, secrets)


def _load_all_encrypted(path: Path) -> dict[str, Any]:
    """Load all secrets from the encrypted fallback file."""
    import base64

    password = _get_machine_password()
    salt = _get_machine_salt()
    key = _derive_key(password, salt)
    f = Fernet(key)
    data = f.decrypt(path.read_bytes())
    return json.loads(data.decode())


def _load_from_encrypted_file(path: Path, name: str) -> str | None:
    """Load a single secret from the encrypted fallback file."""
    try:
        secrets = _load_all_encrypted(path)
        return secrets.get(name)
    except Exception:
        return None


def _save_encrypted_file(path: Path, secrets: dict[str, Any]) -> None:
    """Save secrets to the encrypted fallback file."""
    import base64

    password = _get_machine_password()
    salt = _get_machine_salt()
    key = _derive_key(password, salt)
    f = Fernet(key)
    data = json.dumps(secrets, indent=2).encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(f.encrypt(data))


def _get_machine_password() -> str:
    """Return a machine-bound password for fallback encryption.

    On first use this creates a password file. This is not as secure as
    keyring but is better than plaintext.
    """
    pw_file = CONFIG_DIR / ".machine_pw"
    if pw_file.exists():
        return pw_file.read_text(encoding="utf-8")
    password = os.urandom(32).hex()
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    pw_file.write_text(password, encoding="utf-8")
    return password


# Backwards-compatible migration

def migrate_legacy_api_key() -> str | None:
    """Migrate the legacy api_keys.json file into secure storage."""
    from jarvis.config.paths import LEGACY_CONFIG_FILE

    if not LEGACY_CONFIG_FILE.exists():
        return None

    try:
        data = json.loads(LEGACY_CONFIG_FILE.read_text(encoding="utf-8"))
        key = data.get("gemini_api_key")
        if key:
            set_secret("gemini_api_key", key)
            # Remove the plaintext key from the legacy file
            data.pop("gemini_api_key", None)
            if data:
                LEGACY_CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
            else:
                LEGACY_CONFIG_FILE.unlink()
            return key
    except Exception:
        return None

    return None

