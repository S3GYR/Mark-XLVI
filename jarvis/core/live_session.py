"""Gemini Live audio session management."""

from __future__ import annotations

import asyncio
import re
import threading
from datetime import datetime
from typing import Any

from google import genai
from google.genai import types

from jarvis.audio.capture import AudioCapture
from jarvis.audio.playback import AudioPlayback
from jarvis.audio.phone_relay import PhoneAudioRelay
from jarvis.config.paths import PROMPT_PATH
from jarvis.config.settings import Settings, get_settings
from jarvis.core.player import Player
from jarvis.core.tool_runner import ToolRunner
from jarvis.memory.postgres_store import get_memory_store
from jarvis.observability.logger import get_logger
from jarvis.security.secrets import get_secret

logger = get_logger(__name__)

LIVE_MODEL = "models/gemini-2.5-flash-native-audio-preview-12-2025"
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024

_CTRL_RE = re.compile(r"<ctrl\d+>", re.IGNORECASE)


def _clean_transcript(text: str) -> str:
    text = _CTRL_RE.sub("", text)
    text = re.sub(r"[\x00-\x08\x0b-\x1f]", "", text)
    return text.strip()


def _load_system_prompt() -> str:
    try:
        return PROMPT_PATH.read_text(encoding="utf-8")
    except Exception:
        return (
            "You are JARVIS, Tony Stark's AI assistant. "
            "Be concise, direct, and always use the provided tools to complete tasks. "
            "Never simulate or guess results — always call the appropriate tool."
        )


class GeminiLiveSession:
    """Manages a native Gemini Live audio session."""

    def __init__(self, player: Player, settings: Settings | None = None):
        self.player = player
        self.settings = settings or get_settings()
        self.session = None
        self.audio_in_queue: asyncio.Queue | None = None
        self.out_queue: asyncio.Queue | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._is_speaking = False
        self._speaking_lock = threading.Lock()
        self._phone_active = False
        self._tool_runner = ToolRunner(player)
        self._turn_done_event: asyncio.Event | None = None
        self._tasks: list[asyncio.Task] = []
        self._audio_capture: AudioCapture | None = None
        self._audio_playback: AudioPlayback | None = None
        self._phone_relay: PhoneAudioRelay | None = None

    def _get_api_key(self) -> str:
        key = get_secret("gemini_api_key", env_override="GEMINI_API_KEY")
        if not key:
            raise RuntimeError("Gemini API key not configured")
        return key

    def _build_config(self) -> types.LiveConnectConfig:
        """Build the Gemini Live connection config."""
        now = datetime.now()
        time_str = now.strftime("%A, %B %d, %Y — %I:%M %p")
        time_ctx = (
            f"[CURRENT DATE & TIME]\n"
            f"Right now it is: {time_str}\n"
            f"Use this to calculate exact times for reminders.\n\n"
        )

        parts = [time_ctx]
        # Load memory asynchronously through asyncio.run if needed; here we use JSON sync fallback
        mem_str = self._sync_memory_prompt()
        if mem_str:
            parts.append(mem_str)
        parts.append(_load_system_prompt())

        # Tool declarations from the new registry
        from jarvis.tools.registry import get_tool_declarations

        declarations = [
            {
                "name": decl["function"]["name"],
                "description": decl["function"]["description"],
                "parameters": decl["function"]["parameters"],
            }
            for decl in get_tool_declarations()
        ]
        # Add save_memory tool
        declarations.append({
            "name": "save_memory",
            "description": "Save a fact to long-term memory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string"},
                    "key": {"type": "string"},
                    "value": {"type": "string"},
                },
                "required": ["category", "key", "value"],
            },
        })

        return types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            output_audio_transcription={},
            input_audio_transcription={},
            system_instruction="\n".join(parts),
            tools=[{"function_declarations": declarations}],
            session_resumption=types.SessionResumptionConfig(),
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Charon"
                    )
                )
            ),
        )

    def _sync_memory_prompt(self) -> str:
        """Load memory synchronously for the config builder."""
        try:
            from memory.memory_manager import format_memory_for_prompt, load_memory
            return format_memory_for_prompt(load_memory())
        except Exception:
            return ""

    async def start(self) -> None:
        """Start the Gemini Live session and audio loops."""
        self._loop = asyncio.get_event_loop()
        self.audio_in_queue = asyncio.Queue()
        self.out_queue = asyncio.Queue()
        self._turn_done_event = asyncio.Event()

        client = genai.Client(
            api_key=self._get_api_key(),
            http_options={"api_version": "v1beta"},
        )

        config = self._build_config()
        self.session = client.aio.live.connect(model=LIVE_MODEL, config=config)

        tg = asyncio.TaskGroup()
        async with tg:
            tg.create_task(self._send_realtime())
            tg.create_task(self._listen_audio())
            tg.create_task(self._receive_audio())
            tg.create_task(self._play_audio())

    async def stop(self) -> None:
        """Stop the session and audio tasks."""
        for task in self._tasks:
            task.cancel()
        if self.session:
            await self.session.close()

    def set_speaking(self, value: bool) -> None:
        with self._speaking_lock:
            self._is_speaking = value
        if value:
            self.player.set_state("SPEAKING")
        elif not self.player.muted:
            self.player.set_state("LISTENING")

    def speak(self, text: str) -> None:
        if not self._loop or not self.session:
            return
        asyncio.run_coroutine_threadsafe(
            self.session.send_client_content(
                turns={"parts": [{"text": text}]},
                turn_complete=True,
            ),
            self._loop,
        )

    def on_text_command(self, text: str) -> None:
        if not self._loop or not self.session:
            return
        asyncio.run_coroutine_threadsafe(
            self.session.send_client_content(
                turns={"parts": [{"text": text}]},
                turn_complete=True,
            ),
            self._loop,
        )

    async def _send_realtime(self) -> None:
        while True:
            msg = await self.out_queue.get()
            await self.session.send_realtime_input(media=msg)

    def _enqueue_audio(self, msg: dict) -> None:
        """Callback used by AudioCapture to push frames to the realtime queue."""
        try:
            self.out_queue.put_nowait(msg)
        except Exception as e:
            logger.error("audio_enqueue_error", error=str(e))

    async def _listen_audio(self) -> None:
        """Start the modular microphone capture."""
        loop = asyncio.get_event_loop()
        self._audio_capture = AudioCapture(
            output_callback=self._enqueue_audio,
            is_speaking=lambda: self._is_speaking,
            is_muted=lambda: self.player.muted,
            is_phone_active=lambda: self._phone_active,
            settings=self.settings,
        )
        self._audio_capture.start(loop)
        try:
            while True:
                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            self._audio_capture.stop()
            raise

    async def _receive_audio(self) -> None:
        logger.info("audio_receive_started")
        out_buf, in_buf = [], []

        try:
            while True:
                async for response in self.session.receive():
                    if response.data:
                        if self._turn_done_event and self._turn_done_event.is_set():
                            self._turn_done_event.clear()
                        self.audio_in_queue.put_nowait(response.data)

                    if response.server_content:
                        sc = response.server_content

                        if sc.output_transcription and sc.output_transcription.text:
                            txt = _clean_transcript(sc.output_transcription.text)
                            if txt:
                                out_buf.append(txt)

                        if sc.input_transcription and sc.input_transcription.text:
                            txt = _clean_transcript(sc.input_transcription.text)
                            if txt:
                                in_buf.append(txt)

                        if sc.turn_complete:
                            if out_buf:
                                self.player.write_log("JARVIS: " + " ".join(out_buf))
                                out_buf.clear()
                            if in_buf:
                                self.player.write_log("YOU: " + " ".join(in_buf))
                                in_buf.clear()
                            self.set_speaking(False)

                    if response.tool_call:
                        for fc in response.tool_call.function_calls:
                            await self._handle_tool_call(fc)

        except Exception as e:
            logger.error("audio_receive_error", error=str(e))
            raise

    async def _play_audio(self) -> None:
        """Start the modular audio playback."""
        self._audio_playback = AudioPlayback(
            audio_queue=self.audio_in_queue,
            settings=self.settings,
        )
        self._audio_playback.start()
        try:
            while True:
                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            self._audio_playback.stop()
            raise

    async def _handle_tool_call(self, fc: Any) -> None:
        self.player.set_state("THINKING")

        if fc.name == "save_memory":
            result = self._tool_runner.handle_memory_save(dict(fc.args or {}))
            response = types.FunctionResponse(id=fc.id, name=fc.name, response=result)
        else:
            output = await self._tool_runner.run(fc.name, dict(fc.args or {}))
            response = types.FunctionResponse(id=fc.id, name=fc.name, response={"result": output})

        await self.session.send_tool_response(
            function_responses=[response]
        )

        if not self.player.muted:
            self.player.set_state("LISTENING")
