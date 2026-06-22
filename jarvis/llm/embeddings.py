"""Embedding provider abstraction."""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from typing import Any

from jarvis.config.settings import Settings, get_settings


class EmbeddingProvider(ABC):
    """Abstract embedding provider."""

    @abstractmethod
    def encode(self, text: str) -> list[float]:
        """Return a dense vector for the given text."""
        raise NotImplementedError

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the vector dimension."""
        raise NotImplementedError


class MockEmbeddingProvider(EmbeddingProvider):
    """Deterministic fallback embedding for tests and offline mode."""

    def __init__(self, dim: int = 768):
        self.dim = dim

    def encode(self, text: str) -> list[float]:
        h = hashlib.sha256(text.encode()).digest()
        values = []
        for i in range(self.dim):
            byte = h[i % len(h)]
            values.append((byte / 255.0) * 2 - 1)
        return values

    @property
    def dimension(self) -> int:
        return self.dim


class SentenceTransformerProvider(EmbeddingProvider):
    """Local embeddings via sentence-transformers."""

    def __init__(self, model_name: str, device: str = "cpu", dim: int = 768):
        self.model_name = model_name
        self.device = device
        self._dim = dim
        self._model: Any | None = None

    def _load_model(self) -> Any:
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name, device=self.device)
            self._dim = self._model.get_sentence_embedding_dimension()
        return self._model

    def encode(self, text: str) -> list[float]:
        model = self._load_model()
        return model.encode(text, convert_to_numpy=True, normalize_embeddings=True).tolist()

    @property
    def dimension(self) -> int:
        if self._model is None:
            self._load_model()
        return self._dim


class LiteLLMEmbeddingProvider(EmbeddingProvider):
    """Remote embeddings via LiteLLM."""

    def __init__(self, model: str, api_key: str | None = None, dim: int = 768):
        self.model = model
        self.api_key = api_key
        self._dim = dim

    def encode(self, text: str) -> list[float]:
        import litellm

        kwargs: dict[str, Any] = {
            "model": self.model,
            "input": [text],
        }
        if self.api_key:
            kwargs["api_key"] = self.api_key
        response = litellm.embedding(**kwargs)
        return response["data"][0]["embedding"]

    @property
    def dimension(self) -> int:
        return self._dim


def get_embedding_provider(settings: Settings | None = None) -> EmbeddingProvider:
    """Return the configured embedding provider."""
    settings = settings or get_settings()

    if settings.embedding_provider == "sentence-transformers":
        try:
            return SentenceTransformerProvider(
                model_name=settings.embedding_model,
                device=settings.embedding_device,
                dim=settings.vector_dim,
            )
        except Exception as e:
            if settings.embedding_fallback_to_mock:
                return MockEmbeddingProvider(settings.vector_dim)
            raise RuntimeError(f"Could not load sentence-transformers model: {e}") from e

    if settings.embedding_provider == "litellm":
        from jarvis.security.secrets import get_secret

        api_key = get_secret("litellm_api_key", env_override="LITELLM_API_KEY")
        return LiteLLMEmbeddingProvider(
            model=settings.embedding_model,
            api_key=api_key,
            dim=settings.vector_dim,
        )

    return MockEmbeddingProvider(settings.vector_dim)
