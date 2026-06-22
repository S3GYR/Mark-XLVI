"""Tests for certificate management and dynamic SSL generation."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from pathlib import Path
import ssl


def test_certificate_generation():
    """Test dynamic SSL certificate generation."""
    with patch('jarvis.security.certs.get_settings') as mock_settings:
        mock_settings.return_value.data_dir = Path("/tmp/test_jarvis")
        
        from jarvis.security.certs import ensure_certificates
        
        # Mock certificate creation
        with patch('jarvis.security.certs._generate_cert_pair') as mock_generate:
            mock_generate.return_value = ("cert_content", "key_content")
            
            cert_path, key_path = ensure_certificates()
            
            assert cert_path is not None
            assert key_path is not None
            mock_generate.assert_called_once()


def test_certificate_loading():
    """Test loading existing certificates."""
    with patch('jarvis.security.certs.get_settings') as mock_settings:
        mock_settings.return_value.data_dir = Path("/tmp/test_jarvis")
        
        from jarvis.security.certs import ensure_certificates
        
        # Mock existing certificates
        with patch('jarvis.security.certs._certificates_exist') as mock_exist:
            mock_exist.return_value = True
            
            with patch('jarvis.security.certs._load_certificates') as mock_load:
                mock_load.return_value = ("existing_cert", "existing_key")
                
                cert_path, key_path = ensure_certificates()
                
                assert cert_path == "existing_cert"
                assert key_path == "existing_key"
                mock_load.assert_called_once()


def test_certificate_validation():
    """Test certificate validation."""
    from jarvis.security.certs import _validate_certificate
    
    # Mock valid certificate
    mock_cert = Mock()
    mock_cert.get_subject.return_value = Mock()
    mock_cert.get_issuer.return_value = Mock()
    mock_cert.has_expired.return_value = False
    
    assert _validate_certificate(mock_cert)
    
    # Mock expired certificate
    mock_cert.has_expired.return_value = False
    assert _validate_certificate(mock_cert)


def test_certificate_file_permissions():
    """Test certificate file permissions are secure."""
    with patch('jarvis.security.certs.get_settings') as mock_settings:
        mock_settings.return_value.data_dir = Path("/tmp/test_jarvis")
        
        from jarvis.security.certs import _set_secure_permissions
        
        # Mock file
        mock_file = Path("/tmp/test_cert.pem")
        
        with patch.object(mock_file, 'chmod') as mock_chmod:
            _set_secure_permissions(mock_file)
            mock_chmod.assert_called_with(0o600)  # Owner read/write only


def test_certificate_expiration_check():
    """Test certificate expiration checking."""
    from jarvis.security.certs import _is_certificate_expired
    
    # Mock expired certificate
    mock_cert = Mock()
    mock_cert.has_expired.return_value = True
    
    assert _is_certificate_expired(mock_cert)
    
    # Mock valid certificate
    mock_cert.has_expired.return_value = False
    
    assert not _is_certificate_expired(mock_cert)


def test_certificate_regeneration():
    """Test certificate regeneration when expired."""
    with patch('jarvis.security.certs.get_settings') as mock_settings:
        mock_settings.return_value.data_dir = Path("/tmp/test_jarvis")
        
        from jarvis.security.certs import ensure_certificates
        
        # Mock expired certificate
        with patch('jarvis.security.certs._certificates_exist') as mock_exist:
            mock_exist.return_value = True
            
            with patch('jarvis.security.certs._is_certificate_expired') as mock_expired:
                mock_expired.return_value = True
                
                with patch('jarvis.security.certs._generate_cert_pair') as mock_generate:
                    mock_generate.return_value = ("new_cert", "new_key")
                    
                    cert_path, key_path = ensure_certificates()
                    
                    assert cert_path == "new_cert"
                    assert key_path == "new_key"
                    mock_generate.assert_called_once()


def test_ssl_context_creation():
    """Test SSL context creation with generated certificates."""
    with patch('jarvis.security.certs.get_settings') as mock_settings:
        mock_settings.return_value.data_dir = Path("/tmp/test_jarvis")
        
        from jarvis.security.certs import create_ssl_context
        
        # Mock certificate paths
        cert_path = "/tmp/test_cert.pem"
        key_path = "/tmp/test_key.pem"
        
        with patch('ssl.create_default_context') as mock_create_context:
            mock_context = Mock()
            mock_create_context.return_value = mock_context
            
            context = create_ssl_context(cert_path, key_path)
            
            assert context == mock_context
            mock_context.load_cert_chain.assert_called_once_with(cert_path, key_path)


def test_certificate_backup():
    """Test certificate backup functionality."""
    with patch('jarvis.security.certs.get_settings') as mock_settings:
        mock_settings.return_value.data_dir = Path("/tmp/test_jarvis")
        
        from jarvis.security.certs import _backup_certificates
        
        # Mock backup operation
        with patch('shutil.copy2') as mock_copy:
            _backup_certificates("/tmp/source_cert", "/tmp/source_key")
            
            assert mock_copy.call_count == 2


def test_certificate_cleanup():
    """Test cleanup of old certificates."""
    with patch('jarvis.security.certs.get_settings') as mock_settings:
        mock_settings.return_value.data_dir = Path("/tmp/test_jarvis")
        
        from jarvis.security.certs import _cleanup_old_certificates
        
        # Mock cleanup
        with patch('jarvis.security.certs._get_old_certificates') as mock_get_old:
            mock_get_old.return_value = [Path("/tmp/old_cert1.pem"), Path("/tmp/old_cert2.pem")]
            
            with patch('os.remove') as mock_remove:
                _cleanup_old_certificates()
                
                assert mock_remove.call_count == 2


def test_certificate_error_handling():
    """Test error handling in certificate operations."""
    with patch('jarvis.security.certs.get_settings') as mock_settings:
        mock_settings.return_value.data_dir = Path("/tmp/test_jarvis")
        
        from jarvis.security.certs import ensure_certificates
        
        # Test generation error
        with patch('jarvis.security.certs._generate_cert_pair') as mock_generate:
            mock_generate.side_effect = Exception("Certificate generation failed")
            
            with pytest.raises(Exception):
                ensure_certificates()


def test_certificate_directory_creation():
    """Test certificate directory creation."""
    with patch('jarvis.security.certs.get_settings') as mock_settings:
        mock_settings.return_value.data_dir = Path("/tmp/test_jarvis")
        
        from jarvis.security.certs import _ensure_cert_directory
        
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            _ensure_cert_directory()
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)


def test_certificate_subject_generation():
    """Test certificate subject generation."""
    from jarvis.security.certs import _generate_certificate_subject
    
    subject = _generate_certificate_subject()
    
    assert hasattr(subject, 'CN')  # Common Name
    assert hasattr(subject, 'O')   # Organization
    assert hasattr(subject, 'OU')  # Organizational Unit


def test_certificate_key_generation():
    """Test private key generation."""
    from jarvis.security.certs import _generate_private_key
    
    # Mock key generation
    with patch('cryptography.hazmat.primitives.asymmetric.rsa.generate_private_key') as mock_generate:
        mock_key = Mock()
        mock_generate.return_value = mock_key
        
        key = _generate_private_key()
        
        assert key == mock_key
        mock_generate.assert_called_once()


def test_certificate_serialization():
    """Test certificate serialization to PEM format."""
    from jarvis.security.certs import _serialize_certificate
    
    # Mock certificate
    mock_cert = Mock()
    
    with patch('cryptography.hazmat.primitives.serialization.dump_pem') as mock_dump:
        mock_dump.return_value = b"pem_data"
        
        pem_data = _serialize_certificate(mock_cert)
        
        assert pem_data == b"pem_data"
        mock_dump.assert_called_once()


def test_certificate_password_protection():
    """Test that private keys are not password protected."""
    from jarvis.security.certs import _serialize_private_key
    
    # Mock private key
    mock_key = Mock()
    
    with patch('cryptography.hazmat.primitives.serialization.dump_pem') as mock_dump:
        mock_dump.return_value = b"key_data"
        
        key_data = _serialize_private_key(mock_key)
        
        assert key_data == b"key_data"
        # Verify no password is used
        call_args = mock_dump.call_args
        assert call_args[1]['encryption_algorithm'] is None


def test_certificate_metadata():
    """Test certificate metadata storage."""
    with patch('jarvis.security.certs.get_settings') as mock_settings:
        mock_settings.return_value.data_dir = Path("/tmp/test_jarvis")
        
        from jarvis.security.certs import _save_certificate_metadata
        
        metadata = {
            "created_at": "2024-01-01T00:00:00Z",
            "expires_at": "2025-01-01T00:00:00Z",
            "serial_number": "12345"
        }
        
        with patch('json.dump') as mock_dump:
            _save_certificate_metadata(metadata)
            mock_dump.assert_called_once()


def test_certificate_loading_error():
    """Test error handling when loading invalid certificates."""
    from jarvis.security.certs import _load_certificate_from_file
    
    # Mock invalid file
    with patch('pathlib.Path.read_text') as mock_read:
        mock_read.side_effect = IOError("File not found")
        
        with pytest.raises(IOError):
            _load_certificate_from_file(Path("/tmp/invalid.pem"))


def test_certificate_auto_rotation():
    """Test automatic certificate rotation before expiration."""
    with patch('jarvis.security.certs.get_settings') as mock_settings:
        mock_settings.return_value.data_dir = Path("/tmp/test_jarvis")
        
        from jarvis.security.certs import _should_rotate_certificate
        
        # Mock certificate close to expiration
        mock_cert = Mock()
        
        with patch('jarvis.security.certs._get_days_until_expiry') as mock_days:
            mock_days.return_value = 7  # 7 days until expiration
            
            assert _should_rotate_certificate(mock_cert)
            
            mock_days.return_value = 30  # 30 days until expiration
            assert not _should_rotate_certificate(mock_cert)
