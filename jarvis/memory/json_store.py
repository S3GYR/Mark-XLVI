"""JSON-backed memory store for fallback and local development."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from jarvis.config.paths import DATA_DIR
from jarvis.config.settings import get_settings
from jarvis.llm.embeddings import EmbeddingProvider, get_embedding_provider
from jarvis.memory.store import MemoryEntry, MemoryStore


class JsonMemoryStore(MemoryStore):
    """Fallback memory store using a JSON file."""

    DEFAULT_CATEGORIES = {
        "identity",
        "preferences",
        "projects",
        "relationships",
        "wishes",
        "notes",
    }

    def __init__(self, path: Path | None = None, embeddings: EmbeddingProvider | None = None):
        self.path = path or (DATA_DIR / "memory.json")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.embeddings = embeddings or get_embedding_provider()

    async def initialize(self) -> None:
        """Ensure the file exists and create a backup."""
        if not self.path.exists():
            self.path.write_text(json.dumps({}, indent=2), encoding="utf-8")
        self._backup()

    def _backup(self) -> None:
        """Create a backup of the memory file."""
        if self.path.exists():
            shutil.copy(self.path, self.path.with_suffix(".json.bak"))

    def _load(self) -> dict[str, dict[str, Any]]:
        """Load the memory file."""
        if not self.path.exists():
            return {cat: {} for cat in self.DEFAULT_CATEGORIES}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        for cat in self.DEFAULT_CATEGORIES:
            data.setdefault(cat, {})
        return data

    def _save(self, data: dict[str, dict[str, Any]]) -> None:
        """Save the memory file atomically."""
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    async def save(
        self,
        category: str,
        key: str,
        value: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Save a memory entry."""
        data = self._load()
        data.setdefault(category, {})
        data[category][key] = {
            "value": value,
            "metadata": metadata or {},
        }
        self._save(data)

    async def get(self, category: str, key: str) -> MemoryEntry | None:
        """Retrieve a specific memory entry."""
        data = self._load()
        entry = data.get(category, {}).get(key)
        if not entry:
            return None
        return MemoryEntry(
            id=None,
            category=category,
            key=key,
            value=entry.get("value", ""),
            metadata=entry.get("metadata", {}),
        )

    async def search(
        self,
        query: str,
        category: str | None = None,
        limit: int = 5,
    ) -> list[MemoryEntry]:
        """Search memory entries by substring."""
        data = self._load()
        results: list[MemoryEntry] = []
        query_lower = query.lower()
        categories = [category] if category else list(data.keys())
        for cat in categories:
            for key, entry in data.get(cat, {}).items():
                value = entry.get("value", "")
                if query_lower in value.lower() or query_lower in key.lower():
                    results.append(
                        MemoryEntry(
                            id=None,
                            category=cat,
                            key=key,
                            value=value,
                            metadata=entry.get("metadata", {}),
                        )
                    )
                if len(results) >= limit:
                    return results
        return results

    async def list_categories(self) -> list[str]:
        """Return all stored categories."""
        return list(self._load().keys())

    async def format_for_prompt(self, max_chars: int = 4000) -> str:
        """Format memories for a system prompt."""
        data = self._load()
        lines: list[str] = []
        total = 0
        for category, entries in data.items():
            for key, entry in entries.items():
                value = entry.get("value", "")
                line = f"[{category}] {key}: {value}"
                if total + len(line) > max_chars:
                    break
                lines.append(line)
                total += len(line) + 1
        return "\n".join(lines)

    async def close(self) -> None:
        """No-op for JSON store."""
        return

    async def _load_async(self) -> dict[str, dict[str, Any]]:
        """Async wrapper for loading."""
        return self._load()
