"""Dynamic self-signed certificate generation for the dashboard."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from ipaddress import ip_address
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from jarvis.config.paths import CONFIG_DIR


CERT_DIR = CONFIG_DIR / "certs"
CERT_FILE = CERT_DIR / "jarvis.crt"
KEY_FILE = CERT_DIR / "jarvis.key"


def ensure_certificates(hostname: str = "jarvis.local") -> tuple[str, str]:
    """Generate or load self-signed certificates for the dashboard.

    Returns the absolute paths to (cert_file, key_file).
    """
    if CERT_FILE.exists() and KEY_FILE.exists():
        return str(CERT_FILE), str(KEY_FILE)

    CERT_DIR.mkdir(parents=True, exist_ok=True)

    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend(),
    )

    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Malibu"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "JARVIS"),
            x509.NameAttribute(NameOID.COMMON_NAME, hostname),
        ]
    )

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=365))
        .add_extension(
            x509.SubjectAlternativeName(
                [
                    x509.DNSName(hostname),
                    x509.DNSName("localhost"),
                    x509.IPAddress(ip_address("127.0.0.1")),
                    x509.IPAddress(ip_address("::1")),
                ]
            ),
            critical=False,
        )
        .sign(key, hashes.SHA256(), default_backend())
    )

    CERT_FILE.write_bytes(
        cert.public_bytes(serialization.Encoding.PEM)
    )
    KEY_FILE.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )

    return str(CERT_FILE), str(KEY_FILE)


def get_certificate_paths() -> tuple[str, str] | None:
    """Return certificate paths if they exist, else None."""
    if CERT_FILE.exists() and KEY_FILE.exists():
        return str(CERT_FILE), str(KEY_FILE)
    return None
