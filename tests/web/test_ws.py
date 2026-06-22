"""Tests for WebSocket endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from jarvis.web.server import DashboardServer


@pytest.fixture
def server() -> DashboardServer:
    return DashboardServer()


@pytest.fixture
def client(server: DashboardServer) -> TestClient:
    return TestClient(server.app)


def test_ws_rejects_invalid_token(client: TestClient):
    """WebSocket rejects an invalid token."""
    from starlette.websockets import WebSocketDisconnect

    with pytest.raises(WebSocketDisconnect):  # noqa: PT012
        with client.websocket_connect("/ws?token=bad-token") as ws:
            ws.receive_json()


def test_ws_accepts_valid_token(client: TestClient, server: DashboardServer):
    """WebSocket accepts a valid token."""
    pin = server.new_key()
    session_key = server.auth.validate_pin(pin, "127.0.0.1")
    assert session_key is not None
    token = server.auth.create_token(session_key)
    with client.websocket_connect(f"/ws?token={token}") as ws:
        assert len(server._clients) == 1
        ws.send_json({"type": "command", "text": "ping"})


def test_ws_command(client: TestClient, server: DashboardServer):
    """WebSocket command is queued and wake callback called."""
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
        with c.websocket_connect(f"/ws?token={token}") as ws:
            ws.send_json({"type": "command", "text": "hello"})
    assert srv.command_queue.get_nowait() == "hello"
    assert called is True


def test_phone_audio_rejects_invalid_token(client: TestClient):
    """Phone audio WebSocket rejects invalid token."""
    with pytest.raises(Exception):  # noqa: B017
        with client.websocket_connect("/ws/phone-audio?token=bad-token") as ws:
            ws.receive_bytes()
