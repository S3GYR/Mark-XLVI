"""Enhanced upload tests for comprehensive coverage (>60%)."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
import tempfile
import os
from pathlib import Path
from fastapi import UploadFile
from fastapi.responses import JSONResponse, FileResponse


def test_uploads_safe_filename():
    """Test filename sanitization function."""
    from jarvis.web.routes.uploads import _safe_filename
    
    # Test normal filename
    assert _safe_filename("document.pdf") == "document.pdf"
    
    # Test filename with special characters
    assert _safe_filename("my document.pdf") == "my document.pdf"
    assert _safe_filename("file@name.pdf") == "file@name.pdf"
    
    # Test filename with dangerous characters
    assert _safe_filename("file<name>.pdf") == "file_name_.pdf"
    assert _safe_filename("file>name>.pdf") == "file_name_.pdf"
    assert _safe_filename('file"name".pdf') == "file_name_.pdf"
    assert _safe_filename("file:name.pdf") == "file_name.pdf"
    assert _safe_filename("file/name.pdf") == "file_name.pdf"
    assert _safe_filename("file\\name.pdf") == "file_name.pdf"
    assert _safe_filename("file|name.pdf") == "file_name.pdf"
    assert _safe_filename("file?name.pdf") == "file_name.pdf"
    assert _safe_filename("file*name.pdf") == "file_name.pdf"
    
    # Test filename with control characters
    assert _safe_filename("file\x00name.pdf") == "filename.pdf"
    assert _safe_filename("file\x1fname.pdf") == "filename.pdf"
    
    # Test filename with dots and spaces
    assert _safe_filename(".hidden.pdf") == "hidden.pdf"
    assert _safe_filename("  spaced.pdf  ") == "spaced.pdf"
    assert _safe_filename("...dots...pdf") == "dots...pdf"
    
    # Test empty or invalid filenames
    assert _safe_filename("") == "upload"
    assert _safe_filename("...") == "upload"
    assert _safe_filename("   ") == "upload"
    assert _safe_filename("<>\"/\\|?*") == "upload"
    
    # Test path traversal attempts
    assert _safe_filename("../../../etc/passwd") == "etc_passwd"
    assert _safe_filename("..\\..\\windows\\system32") == "windows_system32"
    assert _safe_filename("/absolute/path/file.txt") == "file.txt"


def test_uploads_handle_upload_success():
    """Test successful file upload."""
    from jarvis.web.routes.uploads import handle_upload
    
    # Mock dependencies
    mock_request = Mock()
    mock_request.headers = {"authorization": "Bearer valid_token"}
    
    mock_file = Mock(spec=UploadFile)
    mock_file.filename = "test.txt"
    mock_file.content_type = "text/plain"
    mock_file.size = 1024
    
    mock_auth = Mock()
    mock_auth.get_token_from_header.return_value = "valid_token"
    mock_auth.is_valid_token.return_value = True
    
    mock_broadcast = AsyncMock()
    
    with patch('jarvis.web.routes.uploads.get_settings') as mock_settings:
        mock_settings.return_value.dashboard_max_upload_mb = 10
        
        with patch('jarvis.web.routes.uploads.UPLOADS_DIR') as mock_uploads_dir:
            mock_uploads_dir.__truediv__ = Mock(return_value=Path("test_path"))
            mock_uploads_dir.exists.return_value = True
            mock_uploads_dir.mkdir.return_value = None
            
            with patch('aiofiles.open', create=True) as mock_open:
                mock_file_obj = AsyncMock()
                mock_open.return_value.__aenter__.return_value = mock_file_obj
                
                # Run the async function
                result = asyncio.run(handle_upload(
                    mock_request, mock_file, mock_auth, mock_broadcast
                ))
                
                assert isinstance(result, JSONResponse)
                assert result.status_code == 200
                
                # Verify authentication was checked
                mock_auth.get_token_from_header.assert_called_once_with(mock_request)
                mock_auth.is_valid_token.assert_called_once_with("valid_token")


def test_uploads_handle_upload_unauthorized():
    """Test upload with invalid token."""
    from jarvis.web.routes.uploads import handle_upload
    
    # Mock dependencies
    mock_request = Mock()
    mock_request.headers = {"authorization": "Bearer invalid_token"}
    
    mock_file = Mock(spec=UploadFile)
    mock_file.filename = "test.txt"
    
    mock_auth = Mock()
    mock_auth.get_token_from_header.return_value = "invalid_token"
    mock_auth.is_valid_token.return_value = False
    
    mock_broadcast = AsyncMock()
    
    # Run the async function
    result = asyncio.run(handle_upload(
        mock_request, mock_file, mock_auth, mock_broadcast
    ))
    
    assert isinstance(result, JSONResponse)
    assert result.status_code == 401
    
    # Verify authentication was checked
    mock_auth.get_token_from_header.assert_called_once_with(mock_request)
    mock_auth.is_valid_token.assert_called_once_with("invalid_token")


def test_uploads_handle_upload_no_token():
    """Test upload with no token."""
    from jarvis.web.routes.uploads import handle_upload
    
    # Mock dependencies
    mock_request = Mock()
    mock_request.headers = {}
    
    mock_file = Mock(spec=UploadFile)
    mock_file.filename = "test.txt"
    
    mock_auth = Mock()
    mock_auth.get_token_from_header.return_value = ""
    mock_auth.is_valid_token.return_value = False
    
    mock_broadcast = AsyncMock()
    
    # Run the async function
    result = asyncio.run(handle_upload(
        mock_request, mock_file, mock_auth, mock_broadcast
    ))
    
    assert isinstance(result, JSONResponse)
    assert result.status_code == 401


def test_uploads_handle_upload_size_limit():
    """Test upload with file size exceeding limit."""
    from jarvis.web.routes.uploads import handle_upload
    
    # Mock dependencies
    mock_request = Mock()
    mock_request.headers = {"authorization": "Bearer valid_token"}
    
    mock_file = Mock(spec=UploadFile)
    mock_file.filename = "large_file.txt"
    mock_file.size = 20 * 1024 * 1024  # 20MB
    
    mock_auth = Mock()
    mock_auth.get_token_from_header.return_value = "valid_token"
    mock_auth.is_valid_token.return_value = True
    
    mock_broadcast = AsyncMock()
    
    with patch('jarvis.web.routes.uploads.get_settings') as mock_settings:
        mock_settings.return_value.dashboard_max_upload_mb = 10  # 10MB limit
        
        # Run the async function
        result = asyncio.run(handle_upload(
            mock_request, mock_file, mock_auth, mock_broadcast
        ))
        
        assert isinstance(result, JSONResponse)
        assert result.status_code == 413  # Payload Too Large


def test_uploads_handle_upload_forbidden_extensions():
    """Test upload with forbidden file extensions."""
    from jarvis.web.routes.uploads import handle_upload
    
    # Mock dependencies
    mock_request = Mock()
    mock_request.headers = {"authorization": "Bearer valid_token"}
    
    forbidden_files = [
        ("malware.exe", "application/x-executable"),
        ("script.bat", "application/x-msdownload"),
        ("virus.scr", "application/x-msdownload"),
        ("trojan.com", "application/x-msdownload"),
        ("payload.dll", "application/x-msdownload"),
    ]
    
    mock_auth = Mock()
    mock_auth.get_token_from_header.return_value = "valid_token"
    mock_auth.is_valid_token.return_value = True
    
    mock_broadcast = AsyncMock()
    
    with patch('jarvis.web.routes.uploads.get_settings') as mock_settings:
        mock_settings.return_value.dashboard_max_upload_mb = 10
        
        for filename, content_type in forbidden_files:
            mock_file = Mock(spec=UploadFile)
            mock_file.filename = filename
            mock_file.content_type = content_type
            mock_file.size = 1024
            
            # Run the async function
            result = asyncio.run(handle_upload(
                mock_request, mock_file, mock_auth, mock_broadcast
            ))
            
            assert isinstance(result, JSONResponse)
            assert result.status_code == 400  # Bad Request


def test_uploads_handle_upload_path_traversal():
    """Test upload with path traversal attempts in filename."""
    from jarvis.web.routes.uploads import handle_upload
    
    # Mock dependencies
    mock_request = Mock()
    mock_request.headers = {"authorization": "Bearer valid_token"}
    
    traversal_filenames = [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\config",
        "/etc/shadow",
        "C:\\Windows\\System32\\drivers\\etc\\hosts",
        "..%2F..%2F..%2Fetc%2Fpasswd",  # URL encoded
        "..%5c..%5c..%5cwindows%5csystem32",  # URL encoded backslashes
    ]
    
    mock_auth = Mock()
    mock_auth.get_token_from_header.return_value = "valid_token"
    mock_auth.is_valid_token.return_value = True
    
    mock_broadcast = AsyncMock()
    
    with patch('jarvis.web.routes.uploads.get_settings') as mock_settings:
        mock_settings.return_value.dashboard_max_upload_mb = 10
        
        with patch('jarvis.web.routes.uploads.UPLOADS_DIR') as mock_uploads_dir:
            mock_uploads_dir.__truediv__ = Mock(return_value=Path("safe_path"))
            mock_uploads_dir.exists.return_value = True
            
            with patch('aiofiles.open', create=True) as mock_open:
                mock_file_obj = AsyncMock()
                mock_open.return_value.__aenter__.return_value = mock_file_obj
                
                for filename in traversal_filenames:
                    mock_file = Mock(spec=UploadFile)
                    mock_file.filename = filename
                    mock_file.content_type = "text/plain"
                    mock_file.size = 1024
                    
                    # Run the async function
                    result = asyncio.run(handle_upload(
                        mock_request, mock_file, mock_auth, mock_broadcast
                    ))
                    
                    assert isinstance(result, JSONResponse)
                    assert result.status_code == 200
                    
                    # Verify path was sanitized
                    mock_uploads_dir.__truediv__.assert_called()
                    call_args = mock_uploads_dir.__truediv__.call_args[0][0]
                    assert ".." not in str(call_args)
                    assert "\\" not in str(call_args)


def test_uploads_handle_upload_special_filenames():
    """Test upload with special filenames."""
    from jarvis.web.routes.uploads import handle_upload
    
    # Mock dependencies
    mock_request = Mock()
    mock_request.headers = {"authorization": "Bearer valid_token"}
    
    special_filenames = [
        "file with spaces.pdf",
        "file-with-dashes.doc",
        "file_with_underscores.txt",
        "file.with.dots.csv",
        "file'with'quotes.txt",
        'file"with"double"quotes.txt',
        "file@with@symbols.txt",
        "file#with#hash.txt",
        "file with émojis 🎉.txt",
        "файл-на-русском.txt",  # Cyrillic
        "ファイル名.txt",  # Japanese
        "파일명.txt",  # Korean
        "ملف.txt",  # Arabic
    ]
    
    mock_auth = Mock()
    mock_auth.get_token_from_header.return_value = "valid_token"
    mock_auth.is_valid_token.return_value = True
    
    mock_broadcast = AsyncMock()
    
    with patch('jarvis.web.routes.uploads.get_settings') as mock_settings:
        mock_settings.return_value.dashboard_max_upload_mb = 10
        
        with patch('jarvis.web.routes.uploads.UPLOADS_DIR') as mock_uploads_dir:
            mock_uploads_dir.__truediv__ = Mock(return_value=Path("test_path"))
            mock_uploads_dir.exists.return_value = True
            
            with patch('aiofiles.open', create=True) as mock_open:
                mock_file_obj = AsyncMock()
                mock_open.return_value.__aenter__.return_value = mock_file_obj
                
                for filename in special_filenames:
                    mock_file = Mock(spec=UploadFile)
                    mock_file.filename = filename
                    mock_file.content_type = "text/plain"
                    mock_file.size = 1024
                    
                    # Run the async function
                    result = asyncio.run(handle_upload(
                        mock_request, mock_file, mock_auth, mock_broadcast
                    ))
                    
                    assert isinstance(result, JSONResponse)
                    assert result.status_code == 200


def test_uploads_handle_upload_empty_file():
    """Test upload with empty file."""
    from jarvis.web.routes.uploads import handle_upload
    
    # Mock dependencies
    mock_request = Mock()
    mock_request.headers = {"authorization": "Bearer valid_token"}
    
    mock_file = Mock(spec=UploadFile)
    mock_file.filename = "empty.txt"
    mock_file.content_type = "text/plain"
    mock_file.size = 0
    
    mock_auth = Mock()
    mock_auth.get_token_from_header.return_value = "valid_token"
    mock_auth.is_valid_token.return_value = True
    
    mock_broadcast = AsyncMock()
    
    with patch('jarvis.web.routes.uploads.get_settings') as mock_settings:
        mock_settings.return_value.dashboard_max_upload_mb = 10
        
        with patch('jarvis.web.routes.uploads.UPLOADS_DIR') as mock_uploads_dir:
            mock_uploads_dir.__truediv__ = Mock(return_value=Path("test_path"))
            mock_uploads_dir.exists.return_value = True
            
            with patch('aiofiles.open', create=True) as mock_open:
                mock_file_obj = AsyncMock()
                mock_open.return_value.__aenter__.return_value = mock_file_obj
                
                # Run the async function
                result = asyncio.run(handle_upload(
                    mock_request, mock_file, mock_auth, mock_broadcast
                ))
                
                assert isinstance(result, JSONResponse)
                assert result.status_code == 200


def test_uploads_handle_upload_io_error():
    """Test upload with I/O errors during file save."""
    from jarvis.web.routes.uploads import handle_upload
    
    # Mock dependencies
    mock_request = Mock()
    mock_request.headers = {"authorization": "Bearer valid_token"}
    
    mock_file = Mock(spec=UploadFile)
    mock_file.filename = "test.txt"
    mock_file.content_type = "text/plain"
    mock_file.size = 1024
    
    mock_auth = Mock()
    mock_auth.get_token_from_header.return_value = "valid_token"
    mock_auth.is_valid_token.return_value = True
    
    mock_broadcast = AsyncMock()
    
    with patch('jarvis.web.routes.uploads.get_settings') as mock_settings:
        mock_settings.return_value.dashboard_max_upload_mb = 10
        
        with patch('jarvis.web.routes.uploads.UPLOADS_DIR') as mock_uploads_dir:
            mock_uploads_dir.__truediv__ = Mock(side_effect=IOError("Disk full"))
            
            # Run the async function
            result = asyncio.run(handle_upload(
                mock_request, mock_file, mock_auth, mock_broadcast
            ))
            
            assert isinstance(result, JSONResponse)
            assert result.status_code == 500  # Internal Server Error


def test_uploads_handle_upload_concurrent():
    """Test concurrent upload handling."""
    from jarvis.web.routes.uploads import handle_upload
    
    async def concurrent_upload(filename):
        # Mock dependencies
        mock_request = Mock()
        mock_request.headers = {"authorization": "Bearer valid_token"}
        
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = filename
        mock_file.content_type = "text/plain"
        mock_file.size = 1024
        
        mock_auth = Mock()
        mock_auth.get_token_from_header.return_value = "valid_token"
        mock_auth.is_valid_token.return_value = True
        
        mock_broadcast = AsyncMock()
        
        with patch('jarvis.web.routes.uploads.get_settings') as mock_settings:
            mock_settings.return_value.dashboard_max_upload_mb = 10
            
            with patch('jarvis.web.routes.uploads.UPLOADS_DIR') as mock_uploads_dir:
                mock_uploads_dir.__truediv__ = Mock(return_value=Path(f"test_path_{filename}"))
                mock_uploads_dir.exists.return_value = True
                
                with patch('aiofiles.open', create=True) as mock_open:
                    mock_file_obj = AsyncMock()
                    mock_open.return_value.__aenter__.return_value = mock_file_obj
                    
                    return await handle_upload(mock_request, mock_file, mock_auth, mock_broadcast)
    
    # Run concurrent uploads
    tasks = [concurrent_upload(f"file_{i}.txt") for i in range(5)]
    results = asyncio.run(asyncio.gather(*tasks))
    
    # All should succeed
    for result in results:
        assert isinstance(result, JSONResponse)
        assert result.status_code == 200


def test_uploads_directory_creation():
    """Test uploads directory creation."""
    from jarvis.web.routes.uploads import UPLOADS_DIR
    from jarvis.config.paths import DATA_DIR
    
    # Verify UPLOADS_DIR is properly configured
    assert UPLOADS_DIR == DATA_DIR / "uploads"
    
    # Directory should exist or be creatable
    if not UPLOADS_DIR.exists():
        try:
            UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
            assert UPLOADS_DIR.exists()
        except Exception:
            pytest.skip("Cannot create uploads directory")


def test_uploads_file_operations():
    """Test file operations in uploads directory."""
    from jarvis.web.routes.uploads import UPLOADS_DIR, _safe_filename
    
    # Test safe filename with actual file operations
    test_filenames = [
        "normal_file.txt",
        "file with spaces.pdf",
        "file<with>brackets.doc",
        "path/traversal/attempt.txt",
        "file\x00with\x01control\x02chars.txt",
    ]
    
    for filename in test_filenames:
        safe_name = _safe_filename(filename)
        
        # Verify safe name doesn't contain dangerous characters
        dangerous_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*', '\x00']
        for char in dangerous_chars:
            assert char not in safe_name
        
        # Verify safe name is not empty
        assert len(safe_name) > 0
        
        # Verify safe name could be used as a filename
        assert safe_name == safe_name.strip(". ")


def test_uploads_broadcast_functionality():
    """Test broadcast functionality during upload."""
    from jarvis.web.routes.uploads import handle_upload
    
    # Mock dependencies
    mock_request = Mock()
    mock_request.headers = {"authorization": "Bearer valid_token"}
    
    mock_file = Mock(spec=UploadFile)
    mock_file.filename = "test.txt"
    mock_file.content_type = "text/plain"
    mock_file.size = 1024
    
    mock_auth = Mock()
    mock_auth.get_token_from_header.return_value = "valid_token"
    mock_auth.is_valid_token.return_value = True
    
    mock_broadcast = AsyncMock()
    
    with patch('jarvis.web.routes.uploads.get_settings') as mock_settings:
        mock_settings.return_value.dashboard_max_upload_mb = 10
        
        with patch('jarvis.web.routes.uploads.UPLOADS_DIR') as mock_uploads_dir:
            mock_uploads_dir.__truediv__ = Mock(return_value=Path("test_path"))
            mock_uploads_dir.exists.return_value = True
            
            with patch('aiofiles.open', create=True) as mock_open:
                mock_file_obj = AsyncMock()
                mock_open.return_value.__aenter__.return_value = mock_file_obj
                
                # Run the async function
                result = asyncio.run(handle_upload(
                    mock_request, mock_file, mock_auth, mock_broadcast
                ))
                
                assert isinstance(result, JSONResponse)
                assert result.status_code == 200
                
                # Verify broadcast was called
                mock_broadcast.assert_called_once()


def test_uploads_error_handling():
    """Test error handling in upload functions."""
    from jarvis.web.routes.uploads import _safe_filename
    
    # Test _safe_filename with various edge cases
    edge_cases = [
        None,  # type: ignore
        "",  # Empty
        "   ",  # Spaces only
        "...",  # Dots only
        "<>\"/\\|?*",  # Dangerous chars only
        "\x00\x01\x02\x03",  # Control chars only
        "a" * 1000,  # Very long filename
    ]
    
    for case in edge_cases:
        if case is None:
            try:
                _safe_filename(case)  # type: ignore
                assert False, "Should raise exception for None"
            except (TypeError, AttributeError):
                pass  # Expected
        else:
            safe_name = _safe_filename(case)
            assert isinstance(safe_name, str)
            assert len(safe_name) > 0
            assert safe_name != case or case == "upload"  # Should be sanitized or default


def test_uploads_mime_type_handling():
    """Test handling of different MIME types."""
    from jarvis.web.routes.uploads import handle_upload
    
    # Test various MIME types
    mime_types = [
        ("document.pdf", "application/pdf"),
        ("image.jpg", "image/jpeg"),
        ("image.png", "image/png"),
        ("text.txt", "text/plain"),
        ("data.json", "application/json"),
        ("data.csv", "text/csv"),
        ("archive.zip", "application/zip"),
        ("audio.mp3", "audio/mpeg"),
        ("video.mp4", "video/mp4"),
    ]
    
    for filename, content_type in mime_types:
        # Mock dependencies
        mock_request = Mock()
        mock_request.headers = {"authorization": "Bearer valid_token"}
        
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = filename
        mock_file.content_type = content_type
        mock_file.size = 1024
        
        mock_auth = Mock()
        mock_auth.get_token_from_header.return_value = "valid_token"
        mock_auth.is_valid_token.return_value = True
        
        mock_broadcast = AsyncMock()
        
        with patch('jarvis.web.routes.uploads.get_settings') as mock_settings:
            mock_settings.return_value.dashboard_max_upload_mb = 10
            
            with patch('jarvis.web.routes.uploads.UPLOADS_DIR') as mock_uploads_dir:
                mock_uploads_dir.__truediv__ = Mock(return_value=Path("test_path"))
                mock_uploads_dir.exists.return_value = True
                
                with patch('aiofiles.open', create=True) as mock_open:
                    mock_file_obj = AsyncMock()
                    mock_open.return_value.__aenter__.return_value = mock_file_obj
                    
                    # Run the async function
                    result = asyncio.run(handle_upload(
                        mock_request, mock_file, mock_auth, mock_broadcast
                    ))
                    
                    assert isinstance(result, JSONResponse)
                    assert result.status_code == 200
