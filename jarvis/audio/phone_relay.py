"""Phone microphone audio relay for the dashboard."""

from __future__ import annotations

import asyncio
from typing import Callable

from jarvis.observability.logger import get_logger

logger = get_logger(__name__)


class PhoneAudioRelay:
    """Relay audio received from a phone WebSocket into the Gemini Live pipeline."""

    def __init__(
        self,
        output_callback: Callable[[dict], None],
        max_queue_size: int = 200,
    ):
        self.output_callback = output_callback
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start forwarding phone audio frames."""
        self._running = True
        self._task = asyncio.create_task(self._forward())
        logger.info("phone_relay_started")

    async def stop(self) -> None:
        """Stop forwarding phone audio frames."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _forward(self) -> None:
        while self._running:
            try:
                data = await self.queue.get()
                self.output_callback(data)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("phone_relay_forward_error", error=str(e))

    async def put(self, data: bytes) -> None:
        """Receive a raw audio chunk from the phone."""
        try:
            self.queue.put_nowait({"data": data, "mime_type": "audio/pcm"})
        except asyncio.QueueFull:
            logger.warning("phone_relay_queue_full")
