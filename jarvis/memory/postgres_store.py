"""PostgreSQL + pgvector memory store implementation."""

from __future__ import annotations

import json
import uuid
from typing import Any

import psycopg
from psycopg import sql

from jarvis.config.settings import Settings, get_settings
from jarvis.llm.embeddings import EmbeddingProvider, get_embedding_provider
from jarvis.memory.store import MemoryEntry, MemoryStore


CREATE_SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    embedding VECTOR(768),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(category, key)
);

CREATE INDEX IF NOT EXISTS idx_memories_category
    ON memories(category);

CREATE INDEX IF NOT EXISTS idx_memories_key
    ON memories(key);

CREATE INDEX IF NOT EXISTS idx_memories_embedding
    ON memories USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
"""


class PostgresMemoryStore(MemoryStore):
    """Memory store backed by PostgreSQL and pgvector."""

    def __init__(self, dsn: str | None = None, embeddings: EmbeddingProvider | None = None):
        self.dsn = dsn or self._build_dsn()
        self.embeddings = embeddings or get_embedding_provider()
        self._pool: psycopg.AsyncConnection | None = None

    def _build_dsn(self) -> str:
        """Build a PostgreSQL DSN from settings or environment."""
        settings = get_settings()
        if settings.postgres_url:
            return settings.postgres_url
        # Fallback defaults
        host = "localhost"
        port = 5432
        dbname = "jarvis"
        user = "jarvis"
        password = "jarvis"
        return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"

    async def initialize(self) -> None:
        """Create schema and indexes."""
        conn = await psycopg.AsyncConnection.connect(self.dsn)
        await conn.execute(CREATE_SCHEMA_SQL)
        await conn.commit()
        await conn.close()

    async def _connect(self) -> psycopg.AsyncConnection:
        """Return a connection (create one if needed)."""
        if self._pool is None or self._pool.closed:
            self._pool = await psycopg.AsyncConnection.connect(self.dsn)
        return self._pool

    async def save(
        self,
        category: str,
        key: str,
        value: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Save a memory entry, generating an embedding if possible."""
        embedding = await self._generate_embedding(value)
        meta = json.dumps(metadata or {})
        conn = await self._connect()
        await conn.execute(
            """
            INSERT INTO memories (id, category, key, value, metadata, embedding)
            VALUES (gen_random_uuid(), %s, %s, %s, %s, %s)
            ON CONFLICT (category, key)
            DO UPDATE SET
                value = EXCLUDED.value,
                metadata = EXCLUDED.metadata,
                embedding = EXCLUDED.embedding,
                updated_at = NOW()
            """,
            (category, key, value, meta, embedding),
        )
        await conn.commit()

    async def get(self, category: str, key: str) -> MemoryEntry | None:
        """Retrieve a specific memory entry."""
        conn = await self._connect()
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT id, value, metadata, embedding FROM memories WHERE category = %s AND key = %s",
                (category, key),
            )
            row = await cur.fetchone()
            if not row:
                return None
            return MemoryEntry(
                id=str(row[0]),
                category=category,
                key=key,
                value=row[1],
                metadata=row[2],
                embedding=row[3],
            )

    async def search(
        self,
        query: str,
        category: str | None = None,
        limit: int = 5,
    ) -> list[MemoryEntry]:
        """Search memories by semantic similarity."""
        embedding = await self._generate_embedding(query)
        conn = await self._connect()
        results: list[MemoryEntry] = []
        async with conn.cursor() as cur:
            if embedding:
                if category:
                    await cur.execute(
                        """
                        SELECT id, category, key, value, metadata, embedding,
                               embedding <=> %s::vector AS distance
                        FROM memories
                        WHERE category = %s
                        ORDER BY embedding <=> %s::vector
                        LIMIT %s
                        """,
                        (embedding, category, embedding, limit),
                    )
                else:
                    await cur.execute(
                        """
                        SELECT id, category, key, value, metadata, embedding,
                               embedding <=> %s::vector AS distance
                        FROM memories
                        ORDER BY embedding <=> %s::vector
                        LIMIT %s
                        """,
                        (embedding, embedding, limit),
                    )
            else:
                # Fallback: text search
                pattern = f"%{query}%"
                if category:
                    await cur.execute(
                        """
                        SELECT id, category, key, value, metadata, embedding
                        FROM memories
                        WHERE category = %s AND value ILIKE %s
                        ORDER BY updated_at DESC
                        LIMIT %s
                        """,
                        (category, pattern, limit),
                    )
                else:
                    await cur.execute(
                        """
                        SELECT id, category, key, value, metadata, embedding
                        FROM memories
                        WHERE value ILIKE %s
                        ORDER BY updated_at DESC
                        LIMIT %s
                        """,
                        (pattern, limit),
                    )

            async for row in cur:
                results.append(
                    MemoryEntry(
                        id=str(row[0]),
                        category=row[1],
                        key=row[2],
                        value=row[3],
                        metadata=row[4],
                        embedding=row[5],
                    )
                )
        return results

    async def list_categories(self) -> list[str]:
        """Return all categories."""
        conn = await self._connect()
        async with conn.cursor() as cur:
            await cur.execute("SELECT DISTINCT category FROM memories ORDER BY category")
            rows = await cur.fetchall()
            return [row[0] for row in rows]

    async def format_for_prompt(self, max_chars: int = 4000) -> str:
        """Format the most recent memories for a system prompt."""
        conn = await self._connect()
        lines: list[str] = []
        total = 0
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT category, key, value
                FROM memories
                ORDER BY updated_at DESC
                """
            )
            async for row in cur:
                line = f"[{row[0]}] {row[1]}: {row[2]}"
                if total + len(line) > max_chars:
                    break
                lines.append(line)
                total += len(line) + 1
        return "\n".join(lines)

    async def close(self) -> None:
        """Close the connection."""
        if self._pool and not self._pool.closed:
            await self._pool.close()

    async def _generate_embedding(self, text: str) -> list[float] | None:
        """Generate an embedding vector for the text using the configured provider."""
        try:
            return self.embeddings.encode(text)
        except Exception:
            return None


async def get_memory_store() -> MemoryStore:
    """Factory returning the configured memory store."""
    from jarvis.memory.json_store import JsonMemoryStore

    settings = get_settings()
    if settings.memory_backend == "postgres":
        store: MemoryStore = PostgresMemoryStore()
        await store.initialize()
        return store
    return JsonMemoryStore()
