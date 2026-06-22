"""Tests for embedding providers."""

from __future__ import annotations

import pytest

from jarvis.llm.embeddings import (
    LiteLLMEmbeddingProvider,
    MockEmbeddingProvider,
    SentenceTransformerProvider,
)


def test_mock_embedding_dimension():
    """Mock provider returns the configured dimension."""
    provider = MockEmbeddingProvider(dim=384)
    vec = provider.encode("hello")
    assert len(vec) == 384
    assert provider.dimension == 384


def test_mock_embedding_is_deterministic():
    """Same text produces the same vector."""
    provider = MockEmbeddingProvider(dim=128)
    assert provider.encode("test") == provider.encode("test")
    assert provider.encode("test") != provider.encode("other")


def test_mock_values_normalized():
    """Values are within [-1, 1]."""
    provider = MockEmbeddingProvider(dim=64)
    vec = provider.encode("x")
    assert all(-1 <= v <= 1 for v in vec)


@pytest.mark.skip(reason="Requires sentence-transformers model download")
def test_sentence_transformer_provider():
    """Smoke test for sentence-transformers provider."""
    provider = SentenceTransformerProvider("all-MiniLM-L6-v2")
    vec = provider.encode("hello world")
    assert len(vec) == provider.dimension


def test_litellm_provider_dimension():
    """LiteLLM provider reports the configured dimension."""
    provider = LiteLLMEmbeddingProvider("text-embedding-3-small", dim=1536)
    assert provider.dimension == 1536
