"""Abstract memory store interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class MemoryEntry:
    """A single memory entry."""

    id: str | None
    category: str
    key: str
    value: str
    metadata: dict[str, Any]
    embedding: list[float] | None = None


class MemoryStore(ABC):
    """Abstract base class for memory storage backends."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the store (create tables, indexes, etc.)."""
        raise NotImplementedError

    @abstractmethod
    async def save(self, category: str, key: str, value: str, metadata: dict[str, Any] | None = None) -> None:
        """Save a memory entry."""
        raise NotImplementedError

    @abstractmethod
    async def get(self, category: str, key: str) -> MemoryEntry | None:
        """Get a specific memory entry."""
        raise NotImplementedError

    @abstractmethod
    async def search(self, query: str, category: str | None = None, limit: int = 5) -> list[MemoryEntry]:
        """Search memory entries semantically or by substring."""
        raise NotImplementedError

    @abstractmethod
    async def list_categories(self) -> list[str]:
        """Return all stored categories."""
        raise NotImplementedError

    @abstractmethod
    async def format_for_prompt(self, max_chars: int = 4000) -> str:
        """Format relevant memories for injection into a system prompt."""
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        """Close the store."""
        raise NotImplementedError
