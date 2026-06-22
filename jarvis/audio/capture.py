"""Microphone audio capture for the Gemini Live pipeline."""

from __future__ import annotations

import asyncio
import threading
from typing import Callable

import numpy as np
import sounddevice as sd

from jarvis.config.settings import Settings, get_settings
from jarvis.observability.logger import get_logger

logger = get_logger(__name__)


class AudioCapture:
    """Capture microphone audio and push PCM frames to a callback."""

    def __init__(
        self,
        output_callback: Callable[[dict], None],
        is_speaking: Callable[[], bool],
        is_muted: Callable[[], bool],
        is_phone_active: Callable[[], bool],
        settings: Settings | None = None,
    ):
        self.output_callback = output_callback
        self.is_speaking = is_speaking
        self.is_muted = is_muted
        self.is_phone_active = is_phone_active
        self.settings = settings or get_settings()
        self._stream: sd.InputStream | None = None
        self._running = False

    def start(self, loop: asyncio.AbstractEventLoop) -> None:
        """Start the microphone input stream."""
        self._running = True
        sample_rate = self.settings.audio_send_sample_rate
        channels = self.settings.audio_channels
        chunk_size = self.settings.audio_chunk_size
        device = self.settings.audio_device_index

        def callback(indata: np.ndarray, frames: int, time_info: dict, status: sd.CallbackFlags) -> None:
            if not self._running:
                return
            if self.is_speaking() or self.is_muted() or self.is_phone_active():
                return
            data = indata.astype(np.int16).tobytes()
            loop.call_soon_threadsafe(
                self.output_callback,
                {"data": data, "mime_type": "audio/pcm"},
            )

        try:
            self._stream = sd.InputStream(
                samplerate=sample_rate,
                channels=channels,
                dtype="int16",
                blocksize=chunk_size,
                device=device,
                callback=callback,
            )
            self._stream.start()
            logger.info("audio_capture_started", sample_rate=sample_rate, channels=channels)
        except Exception as e:
            logger.error("audio_capture_error", error=str(e))
            raise

    def stop(self) -> None:
        """Stop the microphone input stream."""
        self._running = False
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception as e:
                logger.error("audio_capture_stop_error", error=str(e))
            self._stream = None
