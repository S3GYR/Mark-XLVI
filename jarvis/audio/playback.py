"""Audio playback for the Gemini Live pipeline."""

from __future__ import annotations

import asyncio

import numpy as np
import sounddevice as sd

from jarvis.config.settings import Settings, get_settings
from jarvis.observability.logger import get_logger

logger = get_logger(__name__)


class AudioPlayback:
    """Play incoming PCM audio frames through the speakers."""

    def __init__(
        self,
        audio_queue: asyncio.Queue,
        settings: Settings | None = None,
    ):
        self.audio_queue = audio_queue
        self.settings = settings or get_settings()
        self._stream: sd.RawOutputStream | None = None
        self._running = False

    def start(self) -> None:
        """Start the audio output stream."""
        self._running = True
        sample_rate = self.settings.audio_receive_sample_rate
        channels = self.settings.audio_channels
        chunk_size = self.settings.audio_chunk_size

        def callback(outdata: np.ndarray, frames: int, time_info: dict, status: sd.CallbackFlags) -> None:
            if not self._running:
                outdata[:] = b"\x00" * (frames * 2)
                return
            try:
                data = self.audio_queue.get_nowait()
                expected = frames * 2  # 16-bit mono
                if len(data) < expected:
                    outdata[: len(data) // 2] = np.frombuffer(data, dtype=np.int16)
                    outdata[len(data) // 2 :] = 0
                else:
                    outdata[:] = np.frombuffer(data[:expected], dtype=np.int16).reshape(-1, 1)
            except asyncio.QueueEmpty:
                outdata[:] = b"\x00" * (frames * 2)

        try:
            self._stream = sd.RawOutputStream(
                samplerate=sample_rate,
                channels=channels,
                dtype="int16",
                blocksize=chunk_size,
                callback=callback,
            )
            self._stream.start()
            logger.info("audio_playback_started", sample_rate=sample_rate, channels=channels)
        except Exception as e:
            logger.error("audio_playback_error", error=str(e))
            raise

    def stop(self) -> None:
        """Stop the audio output stream."""
        self._running = False
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception as e:
                logger.error("audio_playback_stop_error", error=str(e))
            self._stream = None
