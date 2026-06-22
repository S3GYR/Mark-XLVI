"""Tests for the FastAPI dashboard server."""

from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient

from jarvis.web.server import DashboardServer


@pytest.fixture
def server() -> DashboardServer:
    return DashboardServer()


@pytest.fixture
def client(server: DashboardServer) -> TestClient:
    return TestClient(server.app)


def test_login_page(client: TestClient):
    """Login page returns HTML."""
    response = client.get("/login")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_index_page(client: TestClient):
    """Index page returns HTML with placeholders replaced."""
    response = client.get("/")
    assert response.status_code == 200
    assert "127.0.0.1" in response.text


def test_login_success(client: TestClient, server: DashboardServer):
    """Valid PIN returns a token."""
    pin = server.new_key()
    response = client.post("/login", json={"pin": pin})
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "token" in data


def test_login_failure(client: TestClient):
    """Invalid PIN returns 401."""
    response = client.post("/login", json={"pin": "000000"})
    assert response.status_code == 401


def test_auto_login_success(client: TestClient, server: DashboardServer):
    """Auto-login via QR code returns a connecting script."""
    pin = server.new_key()
    response = client.get(f"/auto-login?key={pin}")
    assert response.status_code == 200
    assert "jarvis_token" in response.text


def test_auto_login_failure(client: TestClient):
    """Expired QR code returns an error message."""
    response = client.get("/auto-login?key=000000")
    assert response.status_code == 200
    assert "Link expired" in response.text


def test_device_login_success(client: TestClient, server: DashboardServer):
    """Device token reconnection returns a token."""
    pin = server.new_key()
    session_key = server.auth.validate_pin(pin, "127.0.0.1")
    assert session_key is not None
    device_token = server.auth.create_device_session(session_key)
    response = client.post("/api/device-login", json={"device_token": device_token})
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "token" in data


def test_device_login_failure(client: TestClient):
    """Invalid device token returns 401."""
    response = client.post("/api/device-login", json={"device_token": "bad-token"})
    assert response.status_code == 401


def test_revoke_devices(client: TestClient, server: DashboardServer):
    """Revoke devices requires a valid token."""
    pin = server.new_key()
    session_key = server.auth.validate_pin(pin, "127.0.0.1")
    assert session_key is not None
    token = server.auth.create_token(session_key)
    response = client.post(
        "/api/revoke-devices",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200


def test_revoke_devices_unauthorized(client: TestClient):
    """Revoke devices without token returns 401."""
    response = client.post("/api/revoke-devices")
    assert response.status_code == 401


def test_command_authorized(client: TestClient, server: DashboardServer):
    """Command endpoint accepts a valid token and queues text."""
    pin = server.new_key()
    session_key = server.auth.validate_pin(pin, "127.0.0.1")
    assert session_key is not None
    token = server.auth.create_token(session_key)
    response = client.post(
        "/api/command",
        json={"text": "hello"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert server.command_queue.get_nowait() == "hello"


def test_command_unauthorized(client: TestClient):
    """Command endpoint without token returns 401."""
    response = client.post("/api/command", json={"text": "hello"})
    assert response.status_code == 401


def test_wake_authorized(client: TestClient, server: DashboardServer):
    """Wake endpoint triggers callback when authorized."""
    called = False

    def wake():
        nonlocal called
        called = True

    srv = DashboardServer(wake_callback=wake)
    pin = srv.new_key()
    session_key = srv.auth.validate_pin(pin, "127.0.0.1")
    assert session_key is not None
    token = srv.auth.create_token(session_key)
    with TestClient(srv.app) as c:
        response = c.post(
            "/api/wake",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 200
    assert called is True


def test_wake_unauthorized(client: TestClient):
    """Wake endpoint without token returns 401."""
    response = client.post("/api/wake")
    assert response.status_code == 401


def test_upload_authorized(client: TestClient, server: DashboardServer, tmp_path):
    """Upload endpoint accepts a file with valid token."""
    pin = server.new_key()
    session_key = server.auth.validate_pin(pin, "127.0.0.1")
    assert session_key is not None
    token = server.auth.create_token(session_key)
    content = b"hello world"
    response = client.post(
        "/api/upload",
        files={"file": ("test.txt", content, "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["size"] == len(content)


def test_list_files_authorized(client: TestClient, server: DashboardServer):
    """List files endpoint requires a valid token."""
    pin = server.new_key()
    session_key = server.auth.validate_pin(pin, "127.0.0.1")
    assert session_key is not None
    token = server.auth.create_token(session_key)
    response = client.get(
        "/api/files",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert "files" in response.json()


def test_download_file_authorized(client: TestClient, server: DashboardServer):
    """Download endpoint serves uploaded files via query token."""
    pin = server.new_key()
    session_key = server.auth.validate_pin(pin, "127.0.0.1")
    assert session_key is not None
    token = server.auth.create_token(session_key)
    upload_response = client.post(
        "/api/upload",
        files={"file": ("download.txt", b"content", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert upload_response.status_code == 200
    name = upload_response.json()["name"]
    response = client.get(f"/uploads/{name}?token={token}")
    assert response.status_code == 200
    assert response.content == b"content"


def test_broadcast(server: DashboardServer):
    """Broadcast appends to history and skips dead clients."""
    asyncio.run(server.broadcast({"type": "test"}))
    assert server._history == [{"type": "test"}]


def test_get_url(server: DashboardServer):
    """URL helpers return expected strings."""
    assert server.get_url().startswith("http://")
    assert ":" in server.get_manual_url()
