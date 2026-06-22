"""Tests for JSON memory store."""

from __future__ import annotations

import asyncio
from pathlib import Path
import tempfile

from jarvis.memory.json_store import JsonMemoryStore


async def test_save_and_get():
    """Saving and retrieving a memory entry works."""
    with tempfile.TemporaryDirectory() as tmp:
        store = JsonMemoryStore(Path(tmp) / "memory.json")
        await store.initialize()
        await store.save("preferences", "name", "Tony")
        entry = await store.get("preferences", "name")
        assert entry is not None
        assert entry.value == "Tony"


async def test_search():
    """Search returns matching entries."""
    with tempfile.TemporaryDirectory() as tmp:
        store = JsonMemoryStore(Path(tmp) / "memory.json")
        await store.initialize()
        await store.save("notes", "project", "MARK XLVI")
        results = await store.search("MARK")
        assert len(results) == 1
        assert results[0].value == "MARK XLVI"


async def test_categories():
    """List categories returns stored categories."""
    with tempfile.TemporaryDirectory() as tmp:
        store = JsonMemoryStore(Path(tmp) / "memory.json")
        await store.initialize()
        await store.save("identity", "name", "JARVIS")
        cats = await store.list_categories()
        assert "identity" in cats


def run_async(coro):
    return asyncio.run(coro)


def test_all():
    run_async(test_save_and_get())
    run_async(test_search())
    run_async(test_categories())
