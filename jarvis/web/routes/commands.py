"""Command endpoint for the dashboard."""

from __future__ import annotations

import asyncio
from typing import Any, Callable

from fastapi import Request
from fastapi.responses import JSONResponse

from jarvis.web.crypto import decrypt_aes
from jarvis.web.auth import AuthManager


async def handle_command(
    req: Request,
    auth: AuthManager,
    command_queue: asyncio.Queue,
    wake_callback: Callable | None,
) -> JSONResponse:
    """Handle an encrypted or plaintext command from the dashboard."""
    token = auth.get_token_from_header(req)
    if not auth.is_valid_token(token):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    body = await req.json()
    enc = body.get("enc", "")
    aes_key = auth.get_aes_key(token)
    if enc:
        if not aes_key:
            return JSONResponse({"error": "Key derivation failed"}, status_code=400)
        text = decrypt_aes(enc, aes_key)
        if text is None:
            return JSONResponse({"error": "Decryption failed"}, status_code=400)
    else:
        text = (body.get("text") or "").strip()

    if text:
        await command_queue.put(text)
        if wake_callback:
            wake_callback()

    return JSONResponse({"ok": True})
