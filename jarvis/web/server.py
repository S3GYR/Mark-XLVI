"""FastAPI dashboard server for JARVIS."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Callable

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi import UploadFile, File as FastAPIFile
import uvicorn

from jarvis.config.paths import BASE_DIR
from jarvis.config.settings import get_settings
from jarvis.observability.logger import get_logger
from jarvis.security.certs import ensure_certificates
from jarvis.web.auth import AuthManager
from jarvis.web.routes import commands, uploads, ws

logger = get_logger(__name__)

STATIC_DIR = BASE_DIR / "dashboard" / "static"


def _read_static(name: str) -> str:
    return (STATIC_DIR / name).read_text(encoding="utf-8")


class DashboardServer:
    """Secure dashboard server with modular routes."""

    def __init__(
        self,
        command_queue: asyncio.Queue | None = None,
        wake_callback: Callable | None = None,
        connect_callback: Callable | None = None,
    ):
        self.settings = get_settings()
        self.auth = AuthManager(self.settings)
        self.command_queue = command_queue or asyncio.Queue()
        self.wake_callback = wake_callback
        self.connect_callback = connect_callback
        self._clients: set[WebSocket] = set()
        self._history: list[dict] = []
        self._phone_audio_queue: asyncio.Queue = asyncio.Queue(maxsize=200)
        self.app = self._build_app()

    def _build_app(self) -> FastAPI:
        app = FastAPI(docs_url=None, redoc_url=None)
        self._register_routes(app)
        return app

    def _register_routes(self, app: FastAPI) -> None:
        login_html = _read_static("login.html")
        app_html = _read_static("app.html")

        @app.get("/login", response_class=HTMLResponse)
        async def login_page() -> HTMLResponse:
            return HTMLResponse(login_html)

        @app.get("/", response_class=HTMLResponse)
        async def index() -> HTMLResponse:
            html = app_html.replace("__IP__", "127.0.0.1").replace("__PORT__", str(self.settings.dashboard_port))
            return HTMLResponse(html)

        @app.post("/login")
        async def login(req: Request) -> JSONResponse:
            body = await req.json()
            entered = str(body.get("pin", "")).strip().upper()
            ip = req.client.host if req.client else "unknown"
            session_key = self.auth.validate_pin(entered, ip)
            if session_key:
                token = self.auth.create_token(session_key)
                if self.connect_callback:
                    self.connect_callback()
                await self.broadcast({"type": "sys", "text": "Remote connection established."})
                return JSONResponse({"ok": True, "token": token})
            return JSONResponse({"ok": False, "error": "Invalid or expired key"}, status_code=401)

        @app.get("/auto-login")
        async def auto_login(key: str = "") -> HTMLResponse:
            ip = "qr"
            session_key = self.auth.validate_pin(key, ip)
            if not session_key:
                return HTMLResponse("<h2>Link expired</h2>")
            token = self.auth.create_token(session_key)
            device_token = self.auth.create_device_session(session_key)
            if self.connect_callback:
                self.connect_callback()
            await self.broadcast({"type": "sys", "text": "Remote connection via QR code."})
            script = f"""
            sessionStorage.setItem('jarvis_token','{token}');
            sessionStorage.setItem('jarvis_key','{session_key}');
            localStorage.setItem('jarvis_device_token','{device_token}');
            setTimeout(function(){{location.replace('/')}}, 400);
            """
            return HTMLResponse(f"<script>{script}</script><p>Connecting...</p>")

        @app.post("/api/device-login")
        async def device_login_ep(req: Request) -> JSONResponse:
            try:
                body = await req.json()
            except Exception:
                return JSONResponse({"ok": False}, status_code=400)
            dev_tok = (body.get("device_token") or "").strip()
            session_key = self.auth.validate_device_token(dev_tok)
            if not session_key:
                return JSONResponse({"ok": False}, status_code=401)
            token = self.auth.create_token(session_key)
            if self.connect_callback:
                self.connect_callback()
            await self.broadcast({"type": "sys", "text": "Known device reconnected."})
            return JSONResponse({"ok": True, "token": token, "key": session_key})

        @app.post("/api/revoke-devices")
        async def revoke_devices(req: Request) -> JSONResponse:
            token = self.auth.get_token_from_header(req)
            if not self.auth.is_valid_token(token):
                return JSONResponse({"error": "Unauthorized"}, status_code=401)
            count = self.auth.revoke_devices()
            return JSONResponse({"ok": True, "revoked": count})

        @app.post("/api/command")
        async def command(req: Request) -> JSONResponse:
            return await commands.handle_command(req, self.auth, self.command_queue, self.wake_callback)

        @app.post("/api/wake")
        async def wake(req: Request) -> JSONResponse:
            token = self.auth.get_token_from_header(req)
            if not self.auth.is_valid_token(token):
                return JSONResponse({"error": "Unauthorized"}, status_code=401)
            if self.wake_callback:
                self.wake_callback()
            return JSONResponse({"ok": True})

        @app.post("/api/upload")
        async def upload_file(req: Request, file: UploadFile = FastAPIFile(...)) -> JSONResponse:
            return await uploads.handle_upload(req, file, self.auth, self.broadcast)

        @app.get("/api/files")
        async def list_files(req: Request) -> JSONResponse:
            return await uploads.list_files(req, self.auth)

        @app.get("/uploads/{filename}", response_model=None)
        async def download_file(filename: str, token: str = "") -> FileResponse | JSONResponse:
            return await uploads.download_file(filename, token, self.auth)

        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket, token: str = "") -> None:
            await ws.handle_client_ws(websocket, token, self.auth, self.command_queue, self.wake_callback, self)

        @app.websocket("/ws/phone-audio")
        async def phone_audio_endpoint(websocket: WebSocket, token: str = "") -> None:
            await ws.handle_phone_audio(websocket, token, self.auth, self._phone_audio_queue)

        @app.get("/static/crypto.js")
        async def serve_crypto() -> FileResponse:
            crypto_file = STATIC_DIR / "crypto-js.min.js"
            if crypto_file.exists():
                return FileResponse(str(crypto_file), media_type="application/javascript")
            return FileResponse(str(STATIC_DIR / "crypto.js"), media_type="application/javascript")

    def new_key(self) -> str:
        """Generate a new one-time PIN."""
        return self.auth.new_pin()

    def get_url(self) -> str:
        return f"http://127.0.0.1:{self.settings.dashboard_port}"

    def get_manual_url(self) -> str:
        return f"127.0.0.1:{self.settings.dashboard_port}"

    async def broadcast(self, msg: dict) -> None:
        """Broadcast a message to all connected WebSocket clients."""
        self._history.append(msg)
        if len(self._history) > 300:
            self._history = self._history[-300:]
        dead: set[WebSocket] = set()
        for ws in list(self._clients):
            try:
                await ws.send_json(msg)
            except Exception:
                dead.add(ws)
        self._clients -= dead

    async def serve(self) -> None:
        """Start the uvicorn server."""
        settings = self.settings
        host = settings.dashboard_host
        port = settings.dashboard_port

        if settings.dashboard_host != "127.0.0.1" and settings.dashboard_auto_firewall:
            logger.warning("auto_firewall_enabled", host=host)

        # Generate certificates if HTTPS is requested
        ssl_config = {}
        if settings.dashboard_host != "127.0.0.1":
            cert, key = ensure_certificates()
            ssl_config = {"ssl_keyfile": key, "ssl_certfile": cert}

        config = uvicorn.Config(
            self.app,
            host=host,
            port=port,
            log_level="warning",
            **ssl_config,
        )
        logger.info("dashboard_starting", host=host, port=port)
        await uvicorn.Server(config).serve()


def create_dashboard_server(
    command_queue: asyncio.Queue | None = None,
    wake_callback: Callable | None = None,
    connect_callback: Callable | None = None,
) -> DashboardServer:
    """Factory for the dashboard server."""
    return DashboardServer(command_queue, wake_callback, connect_callback)
