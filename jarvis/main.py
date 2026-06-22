"""New entry point for the modular JARVIS assistant."""

from __future__ import annotations

import asyncio
import signal
import sys
from typing import Any

from jarvis.config.settings import get_settings
from jarvis.core.orchestrator import AgentOrchestrator
from jarvis.core.player import ConsolePlayer
from jarvis.memory.postgres_store import get_memory_store
from jarvis.observability.logger import configure_logging, get_logger
from jarvis.observability.tracing import configure_tracing

logger = get_logger(__name__)


class JarvisAssistant:
    """Minimal modular assistant runner."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.player = ConsolePlayer()
        self.memory: Any | None = None
        self.orchestrator: AgentOrchestrator | None = None
        self._shutdown = asyncio.Event()

    async def setup(self) -> None:
        """Initialize memory, logging, tracing, and orchestrator."""
        configure_logging()
        configure_tracing()
        self.memory = await get_memory_store()
        self.orchestrator = AgentOrchestrator(
            settings=self.settings,
            memory=self.memory,
            player=self.player,
        )
        logger.info("assistant_initialized", model=self.settings.llm_model)

    async def run_command(self, user_input: str) -> str:
        """Run a single text command through the agent orchestrator."""
        if self.orchestrator is None:
            return "Assistant not initialized."
        return await self.orchestrator.run(user_input)

    async def run_interactive(self) -> None:
        """Run a simple interactive CLI loop."""
        await self.setup()
        print(f"JARVIS modular assistant ready. Model: {self.settings.llm_model}")
        print("Type 'exit' to quit.")

        while not self._shutdown.is_set():
            try:
                user_input = input("\n> ")
            except EOFError:
                break
            if user_input.strip().lower() in {"exit", "quit"}:
                break
            response = await self.run_command(user_input)
            print(response)

    def _handle_signal(self, sig: int) -> None:
        """Handle shutdown signals gracefully."""
        logger.info("shutdown_signal_received", signal=sig)
        self._shutdown.set()

    async def shutdown(self) -> None:
        """Cleanup resources."""
        if self.memory:
            await self.memory.close()
        logger.info("assistant_shutdown")


async def main_async() -> None:
    """Async main entry point."""
    assistant = JarvisAssistant()

    def signal_handler(sig: int, _frame: Any) -> None:
        assistant._handle_signal(sig)

    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, signal_handler)
    try:
        await assistant.run_interactive()
    finally:
        await assistant.shutdown()


def main() -> None:
    """Synchronous entry point.

    Use --gui to start the PyQt6 interface, otherwise start the CLI.
    """
    import argparse

    parser = argparse.ArgumentParser(description="JARVIS modular assistant")
    parser.add_argument("--gui", action="store_true", help="Start the PyQt6 GUI")
    args = parser.parse_args()

    if args.gui:
        from jarvis.ui.app import start_gui_app
        sys.exit(start_gui_app())

    asyncio.run(main_async())


if __name__ == "__main__":
    main()
