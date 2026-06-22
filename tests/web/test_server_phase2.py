"""Phase 2 Dashboard Server tests for comprehensive coverage (>75%)."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
import json
from pathlib import Path
from fastapi.testclient import TestClient
from fastapi import Request


def test_dashboard_server_initialization():
    """Test DashboardServer initialization with default parameters."""
    from jarvis.web.server import DashboardServer
    
    server = DashboardServer()
    
    assert server.settings is not None
    assert server.auth is not None
    assert server.command_queue is not None
    assert server.wake_callback is None
    assert server.connect_callback is None
    assert server._clients == set()
    assert server._history == []
    assert server.app is not None


def test_dashboard_server_initialization_with_callbacks():
    """Test DashboardServer initialization with custom callbacks."""
    from jarvis.web.server import DashboardServer
    
    mock_command_queue = AsyncMock()
    mock_wake_callback = Mock()
    mock_connect_callback = Mock()
    
    server = DashboardServer(
        command_queue=mock_command_queue,
        wake_callback=mock_wake_callback,
        connect_callback=mock_connect_callback
    )
    
    assert server.command_queue == mock_command_queue
    assert server.wake_callback == mock_wake_callback
    assert server.connect_callback == mock_connect_callback


def test_dashboard_server_build_app():
    """Test FastAPI app building."""
    from jarvis.web.server import DashboardServer
    
    server = DashboardServer()
    app = server._build_app()
    
    assert app is not None
    assert hasattr(app, 'routes')
    # Verify some routes are registered
    route_paths = [route.path for route in app.routes]
    assert '/' in route_paths
    assert '/login' in route_paths
    assert '/api/command' in route_paths


def test_read_static_function():
    """Test _read_static function."""
    from jarvis.web.server import _read_static
    
    with patch('jarvis.web.server.STATIC_DIR') as mock_static_dir:
        mock_file = Mock()
        mock_file.read_text.return_value = "<html>test</html>"
        mock_static_dir.__truediv__ = Mock(return_value=mock_file)
        
        result = _read_static("test.html")
        
        assert result == "<html>test</html>"
        mock_static_dir.__truediv__.assert_called_once_with("test.html")
        mock_file.read_text.assert_called_once_with(encoding="utf-8")


def test_dashboard_server_new_key():
    """Test new_key method."""
    from jarvis.web.server import DashboardServer
    
    server = DashboardServer()
    
    with patch.object(server.auth, 'new_pin') as mock_new_pin:
        mock_new_pin.return_value = "123456"
        
        result = server.new_key()
        
        assert result == "123456"
        mock_new_pin.assert_called_once()


def test_dashboard_server_get_urls():
    """Test URL generation methods."""
    from jarvis.web.server import DashboardServer
    
    with patch('jarvis.web.server.get_settings') as mock_settings:
        mock_settings.return_value.dashboard_port = 8080
        
        server = DashboardServer()
        
        assert server.get_url() == "http://127.0.0.1:8080"
        assert server.get_manual_url() == "127.0.0.1:8080"


@pytest.mark.asyncio
async def test_dashboard_server_broadcast():
    """Test broadcast message to all clients."""
    from jarvis.web.server import DashboardServer
    
    server = DashboardServer()
    
    # Mock WebSocket clients
    mock_ws1 = Mock()
    mock_ws1.send_json = AsyncMock()
    mock_ws2 = Mock()
    mock_ws2.send_json = AsyncMock()
    mock_ws3 = Mock()
    mock_ws3.send_json = AsyncMock(side_effect=Exception("Connection lost"))
    
    server._clients = {mock_ws1, mock_ws2, mock_ws3}
    
    # Test broadcast
    message = {"type": "test", "data": "hello"}
    await server.broadcast(message)
    
    # Verify message was sent to all clients
    mock_ws1.send_json.assert_called_once_with(message)
    mock_ws2.send_json.assert_called_once_with(message)
    mock_ws3.send_json.assert_called_once_with(message)
    
    # Verify dead client was removed
    assert mock_ws3 not in server._clients
    assert mock_ws1 in server._clients
    assert mock_ws2 in server._clients
    
    # Verify message was added to history
    assert message in server._history


@pytest.mark.asyncio
async def test_dashboard_server_broadcast_history_limit():
    """Test broadcast with history limit enforcement."""
    from jarvis.web.server import DashboardServer
    
    server = DashboardServer()
    
    # Add 300 messages to history
    server._history = [{"id": i} for i in range(300)]
    
    # Broadcast one more message
    await server.broadcast({"id": 300})
    
    # Verify history is limited to 300 most recent
    assert len(server._history) == 300
    assert server._history[-1] == {"id": 300}
    assert server._history[0] == {"id": 1}  # First message removed


@pytest.mark.asyncio
async def test_dashboard_server_serve_http():
    """Test server serving with HTTP configuration."""
    from jarvis.web.server import DashboardServer
    
    with patch('jarvis.web.server.uvicorn') as mock_uvicorn:
        mock_server = AsyncMock()
        mock_uvicorn.Server.return_value = mock_server
        mock_uvicorn.Config.return_value = Mock()
        
        server = DashboardServer()
        server.settings.dashboard_host = "127.0.0.1"
        server.settings.dashboard_port = 8080
        server.settings.dashboard_auto_firewall = False
        
        await server.serve()
        
        mock_uvicorn.Config.assert_called_once()
        mock_uvicorn.Server.assert_called_once()
        mock_server.serve.assert_called_once()


@pytest.mark.asyncio
async def test_dashboard_server_serve_https_with_firewall_warning():
    """Test server serving with HTTPS and firewall warning."""
    from jarvis.web.server import DashboardServer
    
    with patch('jarvis.web.server.uvicorn') as mock_uvicorn, \
         patch('jarvis.web.server.ensure_certificates') as mock_certs, \
         patch('jarvis.web.server.logger') as mock_logger:
        
        mock_certs.return_value = ("cert.pem", "key.pem")
        mock_server = AsyncMock()
        mock_uvicorn.Server.return_value = mock_server
        mock_uvicorn.Config.return_value = Mock()
        
        server = DashboardServer()
        server.settings.dashboard_host = "0.0.0.0"  # Non-localhost
        server.settings.dashboard_port = 8080
        server.settings.dashboard_auto_firewall = True
        
        await server.serve()
        
        # Verify firewall warning was logged
        mock_logger.warning.assert_called_with("auto_firewall_enabled", host="0.0.0.0")
        
        # Verify certificates were generated
        mock_certs.assert_called_once()
        
        # Verify SSL config was used
        call_args = mock_uvicorn.Config.call_args[1]
        assert "ssl_keyfile" in call_args
        assert "ssl_certfile" in call_args


def test_create_dashboard_server_factory():
    """Test factory function for creating dashboard server."""
    from jarvis.web.server import create_dashboard_server, DashboardServer
    
    mock_command_queue = AsyncMock()
    mock_wake_callback = Mock()
    mock_connect_callback = Mock()
    
    server = create_dashboard_server(
        command_queue=mock_command_queue,
        wake_callback=mock_wake_callback,
        connect_callback=mock_connect_callback
    )
    
    assert isinstance(server, DashboardServer)
    assert server.command_queue == mock_command_queue
    assert server.wake_callback == mock_wake_callback
    assert server.connect_callback == mock_connect_callback


def test_dashboard_server_routes_login_page():
    """Test login page route."""
    from jarvis.web.server import DashboardServer
    
    with patch('jarvis.web.server._read_static') as mock_read_static:
        mock_read_static.return_value = "<html>Login</html>"
        
        server = DashboardServer()
        client = TestClient(server.app)
        
        response = client.get("/login")
        
        assert response.status_code == 200
        assert response.text == "<html>Login</html>"


def test_dashboard_server_routes_index_page():
    """Test index page route."""
    from jarvis.web.server import DashboardServer
    
    with patch('jarvis.web.server._read_static') as mock_read_static:
        mock_read_static.return_value = "<html>App __IP__:__PORT__</html>"
        
        server = DashboardServer()
        server.settings.dashboard_port = 8080
        client = TestClient(server.app)
        
        response = client.get("/")
        
        assert response.status_code == 200
        assert "127.0.0.1" in response.text
        assert "8080" in response.text


def test_dashboard_server_routes_login_success():
    """Test successful login route."""
    from jarvis.web.server import DashboardServer
    
    server = DashboardServer()
    
    with patch.object(server.auth, 'validate_pin') as mock_validate, \
         patch.object(server.auth, 'create_token') as mock_create_token, \
         patch.object(server, 'broadcast') as mock_broadcast:
        
        mock_validate.return_value = "session_key_123"
        mock_create_token.return_value = "token_456"
        
        client = TestClient(server.app)
        response = client.post("/login", json={"pin": "123456"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["token"] == "token_456"
        
        mock_validate.assert_called_once_with("123456", "testclient")
        mock_create_token.assert_called_once_with("session_key_123")
        mock_broadcast.assert_called_once()


def test_dashboard_server_routes_login_failure():
    """Test failed login route."""
    from jarvis.web.server import DashboardServer
    
    server = DashboardServer()
    
    with patch.object(server.auth, 'validate_pin') as mock_validate:
        mock_validate.return_value = None
        
        client = TestClient(server.app)
        response = client.post("/login", json={"pin": "wrong_pin"})
        
        assert response.status_code == 401
        data = response.json()
        assert data["ok"] is False
        assert "Invalid or expired key" in data["error"]


def test_dashboard_server_routes_auto_login_success():
    """Test successful auto-login route."""
    from jarvis.web.server import DashboardServer
    
    server = DashboardServer()
    
    with patch.object(server.auth, 'validate_pin') as mock_validate, \
         patch.object(server.auth, 'create_token') as mock_create_token, \
         patch.object(server.auth, 'create_device_session') as mock_device_session, \
         patch.object(server, 'broadcast') as mock_broadcast:
        
        mock_validate.return_value = "session_key_123"
        mock_create_token.return_value = "token_456"
        mock_device_session.return_value = "device_token_789"
        
        client = TestClient(server.app)
        response = client.get("/auto-login?key=123456")
        
        assert response.status_code == 200
        assert "token_456" in response.text
        assert "session_key_123" in response.text
        assert "device_token_789" in response.text


def test_dashboard_server_routes_auto_login_failure():
    """Test failed auto-login route."""
    from jarvis.web.server import DashboardServer
    
    server = DashboardServer()
    
    with patch.object(server.auth, 'validate_pin') as mock_validate:
        mock_validate.return_value = None
        
        client = TestClient(server.app)
        response = client.get("/auto-login?key=wrong_key")
        
        assert response.status_code == 200
        assert "Link expired" in response.text


def test_dashboard_server_routes_device_login_success():
    """Test successful device login route."""
    from jarvis.web.server import DashboardServer
    
    server = DashboardServer()
    
    with patch.object(server.auth, 'validate_device_token') as mock_validate, \
         patch.object(server.auth, 'create_token') as mock_create_token, \
         patch.object(server, 'broadcast') as mock_broadcast:
        
        mock_validate.return_value = "session_key_123"
        mock_create_token.return_value = "token_456"
        
        client = TestClient(server.app)
        response = client.post("/api/device-login", json={"device_token": "device_token_789"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["token"] == "token_456"
        assert data["key"] == "session_key_123"


def test_dashboard_server_routes_device_login_invalid_json():
    """Test device login with invalid JSON."""
    from jarvis.web.server import DashboardServer
    
    server = DashboardServer()
    client = TestClient(server.app)
    
    response = client.post("/api/device-login", data="invalid json")
    
    assert response.status_code == 400
    data = response.json()
    assert data["ok"] is False


def test_dashboard_server_routes_device_login_failure():
    """Test failed device login route."""
    from jarvis.web.server import DashboardServer
    
    server = DashboardServer()
    
    with patch.object(server.auth, 'validate_device_token') as mock_validate:
        mock_validate.return_value = None
        
        client = TestClient(server.app)
        response = client.post("/api/device-login", json={"device_token": "invalid_token"})
        
        assert response.status_code == 401
        data = response.json()
        assert data["ok"] is False


def test_dashboard_server_routes_revoke_devices_success():
    """Test successful device revocation route."""
    from jarvis.web.server import DashboardServer
    
    server = DashboardServer()
    
    with patch.object(server.auth, 'get_token_from_header') as mock_get_token, \
         patch.object(server.auth, 'is_valid_token') as mock_is_valid, \
         patch.object(server.auth, 'revoke_devices') as mock_revoke:
        
        mock_get_token.return_value = "valid_token"
        mock_is_valid.return_value = True
        mock_revoke.return_value = 3
        
        client = TestClient(server.app)
        response = client.post("/api/revoke-devices", headers={"authorization": "Bearer valid_token"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["revoked"] == 3


def test_dashboard_server_routes_revoke_devices_unauthorized():
    """Test device revocation with invalid token."""
    from jarvis.web.server import DashboardServer
    
    server = DashboardServer()
    
    with patch.object(server.auth, 'get_token_from_header') as mock_get_token, \
         patch.object(server.auth, 'is_valid_token') as mock_is_valid:
        
        mock_get_token.return_value = "invalid_token"
        mock_is_valid.return_value = False
        
        client = TestClient(server.app)
        response = client.post("/api/revoke-devices", headers={"authorization": "Bearer invalid_token"})
        
        assert response.status_code == 401
        data = response.json()
        assert "Unauthorized" in data["error"]


def test_dashboard_server_routes_wake_success():
    """Test successful wake route."""
    from jarvis.web.server import DashboardServer
    
    mock_wake_callback = Mock()
    server = DashboardServer(wake_callback=mock_wake_callback)
    
    with patch.object(server.auth, 'get_token_from_header') as mock_get_token, \
         patch.object(server.auth, 'is_valid_token') as mock_is_valid:
        
        mock_get_token.return_value = "valid_token"
        mock_is_valid.return_value = True
        
        client = TestClient(server.app)
        response = client.post("/api/wake", headers={"authorization": "Bearer valid_token"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        mock_wake_callback.assert_called_once()


def test_dashboard_server_routes_wake_unauthorized():
    """Test wake route with invalid token."""
    from jarvis.web.server import DashboardServer
    
    server = DashboardServer()
    
    with patch.object(server.auth, 'get_token_from_header') as mock_get_token, \
         patch.object(server.auth, 'is_valid_token') as mock_is_valid:
        
        mock_get_token.return_value = "invalid_token"
        mock_is_valid.return_value = False
        
        client = TestClient(server.app)
        response = client.post("/api/wake", headers={"authorization": "Bearer invalid_token"})
        
        assert response.status_code == 401
        data = response.json()
        assert "Unauthorized" in data["error"]


def test_dashboard_server_routes_static_crypto():
    """Test static crypto.js route."""
    from jarvis.web.server import DashboardServer
    
    with patch('jarvis.web.server.STATIC_DIR') as mock_static_dir, \
         patch('jarvis.web.server.FileResponse') as mock_file_response:
        
        # Test with crypto-js.min.js exists
        mock_crypto_file = Mock()
        mock_crypto_file.exists.return_value = True
        mock_static_dir.__truediv__ = Mock(return_value=mock_crypto_file)
        mock_file_response.return_value = Mock(status_code=200)
        
        server = DashboardServer()
        client = TestClient(server.app)
        
        response = client.get("/static/crypto.js")
        
        assert response.status_code == 200


def test_dashboard_server_routes_static_crypto_fallback():
    """Test static crypto.js route with fallback."""
    from jarvis.web.server import DashboardServer
    
    with patch('jarvis.web.server.STATIC_DIR') as mock_static_dir, \
         patch('jarvis.web.server.FileResponse') as mock_file_response:
        
        # Test with crypto-js.min.js not exists, fallback to crypto.js
        mock_crypto_min_file = Mock()
        mock_crypto_min_file.exists.return_value = False
        mock_crypto_file = Mock()
        mock_crypto_file.exists.return_value = True
        mock_file_response.return_value = Mock(status_code=200)
        
        def mock_side_effect(path):
            if path == "crypto-js.min.js":
                return mock_crypto_min_file
            elif path == "crypto.js":
                return mock_crypto_file
        
        mock_static_dir.__truediv__ = Mock(side_effect=mock_side_effect)
        
        server = DashboardServer()
        client = TestClient(server.app)
        
        response = client.get("/static/crypto.js")
        
        assert response.status_code == 200


def test_dashboard_server_routes_command_delegation():
    """Test command route delegation to commands module."""
    from jarvis.web.server import DashboardServer
    
    server = DashboardServer()
    
    with patch('jarvis.web.routes.commands.handle_command') as mock_handle:
        mock_handle.return_value = {"ok": True}
        
        client = TestClient(server.app)
        response = client.post("/api/command", json={"command": "test"})
        
        assert response.status_code == 200
        mock_handle.assert_called_once()


def test_dashboard_server_routes_upload_delegation():
    """Test upload route delegation to uploads module."""
    from jarvis.web.server import DashboardServer
    
    server = DashboardServer()
    
    with patch('jarvis.web.routes.uploads.handle_upload') as mock_handle:
        mock_handle.return_value = {"ok": True}
        
        client = TestClient(server.app)
        response = client.post("/api/upload", files={"file": ("test.txt", "content")})
        
        assert response.status_code == 200
        mock_handle.assert_called_once()


def test_dashboard_server_routes_list_files_delegation():
    """Test list files route delegation to uploads module."""
    from jarvis.web.server import DashboardServer
    
    server = DashboardServer()
    
    with patch('jarvis.web.routes.uploads.list_files') as mock_handle:
        mock_handle.return_value = {"files": []}
        
        client = TestClient(server.app)
        response = client.get("/api/files")
        
        assert response.status_code == 200
        mock_handle.assert_called_once()


def test_dashboard_server_routes_download_delegation():
    """Test download file route delegation to uploads module."""
    from jarvis.web.server import DashboardServer
    
    server = DashboardServer()
    
    with patch('jarvis.web.routes.uploads.download_file') as mock_handle:
        mock_handle.return_value = {"ok": True}
        
        client = TestClient(server.app)
        response = client.get("/uploads/test.txt?token=valid_token")
        
        assert response.status_code == 200
        mock_handle.assert_called_once()


def test_dashboard_server_websocket_endpoints():
    """Test WebSocket endpoint registration."""
    from jarvis.web.server import DashboardServer
    
    server = DashboardServer()
    
    # Check that WebSocket routes are registered
    route_paths = [route.path for route in server.app.routes if hasattr(route, 'path')]
    assert "/ws" in route_paths
    assert "/ws/phone-audio" in route_paths


def test_dashboard_server_error_handling():
    """Test error handling in various scenarios."""
    from jarvis.web.server import DashboardServer
    
    server = DashboardServer()
    
    # Test with missing static files
    with patch('jarvis.web.server._read_static') as mock_read_static:
        mock_read_static.side_effect = FileNotFoundError("Static file not found")
        
        client = TestClient(server.app)
        
        # Should handle gracefully
        with pytest.raises(FileNotFoundError):
            client.get("/login")


def test_dashboard_server_connect_callback_execution():
    """Test that connect callback is executed when appropriate."""
    from jarvis.web.server import DashboardServer
    
    mock_connect_callback = Mock()
    server = DashboardServer(connect_callback=mock_connect_callback)
    
    with patch.object(server.auth, 'validate_pin') as mock_validate, \
         patch.object(server.auth, 'create_token') as mock_create_token, \
         patch.object(server, 'broadcast') as mock_broadcast:
        
        mock_validate.return_value = "session_key"
        mock_create_token.return_value = "token"
        
        client = TestClient(server.app)
        client.post("/login", json={"pin": "123456"})
        
        mock_connect_callback.assert_called_once()


def test_dashboard_server_wake_callback_execution():
    """Test that wake callback is executed when appropriate."""
    from jarvis.web.server import DashboardServer
    
    mock_wake_callback = Mock()
    server = DashboardServer(wake_callback=mock_wake_callback)
    
    with patch.object(server.auth, 'get_token_from_header') as mock_get_token, \
         patch.object(server.auth, 'is_valid_token') as mock_is_valid:
        
        mock_get_token.return_value = "valid_token"
        mock_is_valid.return_value = True
        
        client = TestClient(server.app)
        client.post("/api/wake", headers={"authorization": "Bearer valid_token"})
        
        mock_wake_callback.assert_called_once()


def test_dashboard_server_import():
    """Test that server module imports correctly."""
    try:
        from jarvis.web.server import DashboardServer, create_dashboard_server, _read_static
        assert DashboardServer is not None
        assert create_dashboard_server is not None
        assert _read_static is not None
    except ImportError:
        pytest.fail("Failed to import server module")


def test_dashboard_server_class_structure():
    """Test DashboardServer class structure."""
    from jarvis.web.server import DashboardServer
    import inspect
    
    # Check class has expected methods
    assert hasattr(DashboardServer, '__init__')
    assert hasattr(DashboardServer, '_build_app')
    assert hasattr(DashboardServer, '_register_routes')
    assert hasattr(DashboardServer, 'new_key')
    assert hasattr(DashboardServer, 'get_url')
    assert hasattr(DashboardServer, 'get_manual_url')
    assert hasattr(DashboardServer, 'broadcast')
    assert hasattr(DashboardServer, 'serve')
    
    # Check async methods
    assert inspect.iscoroutinefunction(DashboardServer.broadcast)
    assert inspect.iscoroutinefunction(DashboardServer.serve)
