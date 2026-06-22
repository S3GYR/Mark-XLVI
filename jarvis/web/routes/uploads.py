"""File upload and download endpoints for the dashboard."""

from __future__ import annotations

import asyncio
import re
from pathlib import Path

from fastapi import Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from jarvis.config.paths import DATA_DIR
from jarvis.config.settings import get_settings
from jarvis.web.auth import AuthManager


UPLOADS_DIR = DATA_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


def _safe_filename(raw: str) -> str:
    """Sanitize an uploaded filename."""
    name = Path(raw).name
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(". ")
    return name or "upload"


async def handle_upload(
    req: Request,
    file: UploadFile,
    auth: AuthManager,
    broadcast: asyncio.coroutine,
) -> JSONResponse:
    """Handle a file upload with size limits."""
    token = auth.get_token_from_header(req)
    if not auth.is_valid_token(token):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    settings = get_settings()
    max_bytes = settings.dashboard_max_upload_mb * 1024 * 1024
    safe = _safe_filename(file.filename or "upload")
    dest = UPLOADS_DIR / safe
    stem, suffix = Path(safe).stem, Path(safe).suffix
    counter = 1
    while dest.exists():
        dest = UPLOADS_DIR / f"{stem}_{counter}{suffix}"
        counter += 1

    size = 0
    try:
        with open(dest, "wb") as fout:
            while True:
                chunk = await file.read(65536)
                if not chunk:
                    break
                size += len(chunk)
                if size > max_bytes:
                    dest.unlink(missing_ok=True)
                    return JSONResponse(
                        {"error": f"File too large (max {settings.dashboard_max_upload_mb} MB)"},
                        status_code=413,
                    )
                fout.write(chunk)
    except Exception as exc:
        dest.unlink(missing_ok=True)
        return JSONResponse({"error": str(exc)}, status_code=500)

    await broadcast({
        "type": "file_received",
        "name": dest.name,
        "size": size,
        "saved_to": str(UPLOADS_DIR),
    })
    return JSONResponse({"ok": True, "name": dest.name, "size": size})


async def list_files(req: Request, auth: AuthManager) -> JSONResponse:
    """List uploaded files."""
    token = auth.get_token_from_header(req)
    if not auth.is_valid_token(token):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    files = []
    try:
        for f in sorted(
            (p for p in UPLOADS_DIR.iterdir() if p.is_file()),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        ):
            files.append({"name": f.name, "size": f.stat().st_size})
    except Exception:
        pass
    return JSONResponse({"files": files})


async def download_file(
    filename: str,
    token: str,
    auth: AuthManager,
) -> FileResponse | JSONResponse:
    """Serve an uploaded file via query-param token."""
    if not auth.is_valid_token(token):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    safe = re.sub(r'[/\\]', "", filename)
    path = UPLOADS_DIR / safe
    if not path.exists() or not path.is_file():
        return JSONResponse({"error": "Not found"}, status_code=404)
    return FileResponse(str(path), filename=safe)
