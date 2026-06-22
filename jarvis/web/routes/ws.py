"""WebSocket endpoints for the dashboard."""

from __future__ import annotations

import asyncio
from typing import Any, Callable

from fastapi import WebSocket, WebSocketDisconnect

from jarvis.web.crypto import decrypt_aes
from jarvis.web.auth import AuthManager


async def handle_client_ws(
    websocket: WebSocket,
    token: str,
    auth: AuthManager,
    command_queue: asyncio.Queue,
    wake_callback: Callable | None,
    server: Any,
) -> None:
    """Handle the main dashboard WebSocket."""
    if not auth.is_valid_token(token):
        await websocket.close(code=4001)
        return

    await websocket.accept()
    server._clients.add(websocket)
    for entry in server._history[-50:]:
        try:
            await websocket.send_json(entry)
        except Exception:
            break

    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "command":
                aes_key = auth.get_aes_key(token)
                enc = data.get("enc", "")
                if enc and aes_key:
                    text = decrypt_aes(enc, aes_key) or ""
                else:
                    text = (data.get("text") or "").strip()
                if text:
                    await command_queue.put(text)
                    if wake_callback:
                        wake_callback()
    except WebSocketDisconnect:
        pass
    except asyncio.CancelledError:
        pass
    except ConnectionResetError:
        pass
    except Exception as e:
        # Log unexpected errors but don't crash
        pass
    finally:
        server._clients.discard(websocket)


async def handle_phone_audio(
    websocket: WebSocket,
    token: str,
    auth: AuthManager,
    audio_queue: asyncio.Queue,
) -> None:
    """Handle real-time phone microphone audio streaming."""
    if not auth.is_valid_token(token):
        await websocket.close(code=4001)
        return

    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_bytes()
            try:
                audio_queue.put_nowait({"data": data, "mime_type": "audio/pcm"})
            except asyncio.QueueFull:
                pass
    except WebSocketDisconnect:
        pass
    except asyncio.CancelledError:
        pass
    except ConnectionResetError:
        pass
    except Exception as e:
        # Log unexpected errors but don't crash
        pass
