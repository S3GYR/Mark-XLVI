"""Working tests for embeddings module focusing on existing functionality."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import hashlib
from typing import Any


def test_embeddings_import():
    """Test that embeddings module imports correctly."""
    try:
        import jarvis.llm.embeddings
        assert jarvis.llm.embeddings is not None
    except ImportError:
        pytest.fail("Failed to import jarvis.llm.embeddings")


def test_embedding_provider_import():
    """Test that EmbeddingProvider class imports correctly."""
    try:
        from jarvis.llm.embeddings import EmbeddingProvider
        assert EmbeddingProvider is not None
    except ImportError:
        pytest.fail("Failed to import EmbeddingProvider")


def test_embedding_provider_abstract():
    """Test that EmbeddingProvider is abstract."""
    from jarvis.llm.embeddings import EmbeddingProvider
    
    # Should not be able to instantiate abstract class
    with pytest.raises(TypeError):
        EmbeddingProvider()


def test_mock_embedding_provider_import():
    """Test that MockEmbeddingProvider class imports correctly."""
    try:
        from jarvis.llm.embeddings import MockEmbeddingProvider
        assert MockEmbeddingProvider is not None
    except ImportError:
        pytest.fail("Failed to import MockEmbeddingProvider")


def test_mock_embedding_provider_initialization():
    """Test MockEmbeddingProvider initialization."""
    from jarvis.llm.embeddings import MockEmbeddingProvider
    
    # Test default dimension
    provider = MockEmbeddingProvider()
    assert provider.dim == 768
    assert provider.dimension == 768
    
    # Test custom dimension
    provider = MockEmbeddingProvider(dim=512)
    assert provider.dim == 512
    assert provider.dimension == 512


def test_mock_embedding_provider_encode():
    """Test MockEmbeddingProvider encode method."""
    from jarvis.llm.embeddings import MockEmbeddingProvider
    
    provider = MockEmbeddingProvider(dim=10)
    
    # Test encoding
    result = provider.encode("test text")
    
    assert isinstance(result, list)
    assert len(result) == 10
    assert all(isinstance(x, float) for x in result)
    assert all(-1.0 <= x <= 1.0 for x in result)


def test_mock_embedding_provider_deterministic():
    """Test MockEmbeddingProvider produces deterministic results."""
    from jarvis.llm.embeddings import MockEmbeddingProvider
    
    provider = MockEmbeddingProvider(dim=10)
    
    # Test deterministic encoding
    result1 = provider.encode("test text")
    result2 = provider.encode("test text")
    
    assert result1 == result2
    
    # Test different texts produce different results
    result3 = provider.encode("different text")
    assert result1 != result3


def test_mock_embedding_provider_hash_based():
    """Test MockEmbeddingProvider uses hash-based encoding."""
    from jarvis.llm.embeddings import MockEmbeddingProvider
    
    provider = MockEmbeddingProvider(dim=10)
    
    # Test with known input
    text = "test"
    result = provider.encode(text)
    
    # Verify it's based on SHA256 hash
    h = hashlib.sha256(text.encode()).digest()
    expected_values = []
    for i in range(10):
        byte = h[i % len(h)]
        expected_values.append((byte / 255.0) * 2 - 1)
    
    assert result == expected_values


def test_sentence_transformer_provider_import():
    """Test that SentenceTransformerProvider class imports correctly."""
    try:
        from jarvis.llm.embeddings import SentenceTransformerProvider
        assert SentenceTransformerProvider is not None
    except ImportError:
        pytest.fail("Failed to import SentenceTransformerProvider")


def test_sentence_transformer_provider_initialization():
    """Test SentenceTransformerProvider initialization."""
    from jarvis.llm.embeddings import SentenceTransformerProvider
    
    provider = SentenceTransformerProvider(
        model_name="all-MiniLM-L6-v2",
        device="cpu",
        dim=384
    )
    
    assert provider.model_name == "all-MiniLM-L6-v2"
    assert provider.device == "cpu"
    assert provider._dim == 384
    assert provider._model is None


def test_sentence_transformer_provider_dimension_property():
    """Test SentenceTransformerProvider dimension property."""
    from jarvis.llm.embeddings import SentenceTransformerProvider
    
    provider = SentenceTransformerProvider(
        model_name="all-MiniLM-L6-v2",
        device="cpu",
        dim=384
    )
    
    # Test dimension before model loading
    assert provider.dimension == 384  # Should return _dim


def test_sentence_transformer_provider_load_model():
    """Test SentenceTransformerProvider _load_model method."""
    with patch('jarvis.llm.embeddings.SentenceTransformer') as mock_st:
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_st.return_value = mock_model
        
        from jarvis.llm.embeddings import SentenceTransformerProvider
        
        provider = SentenceTransformerProvider(
            model_name="all-MiniLM-L6-v2",
            device="cpu",
            dim=384
        )
        
        # Test model loading
        model = provider._load_model()
        
        assert model == mock_model
        assert provider._model == mock_model
        assert provider._dim == 384
        
        mock_st.assert_called_once_with("all-MiniLM-L6-v2", device="cpu")
        mock_model.get_sentence_embedding_dimension.assert_called_once()


def test_sentence_transformer_provider_encode():
    """Test SentenceTransformerProvider encode method."""
    with patch('jarvis.llm.embeddings.SentenceTransformer') as mock_st:
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_model.encode.return_value = [0.1, 0.2, 0.3]
        mock_st.return_value = mock_model
        
        from jarvis.llm.embeddings import SentenceTransformerProvider
        
        provider = SentenceTransformerProvider(
            model_name="all-MiniLM-L6-v2",
            device="cpu",
            dim=384
        )
        
        # Test encoding
        result = provider.encode("test text")
        
        assert result == [0.1, 0.2, 0.3]
        mock_model.encode.assert_called_once_with(
            "test text",
            convert_to_numpy=True,
            normalize_embeddings=True
        )


def test_litellm_embedding_provider_import():
    """Test that LiteLLMEmbeddingProvider class imports correctly."""
    try:
        from jarvis.llm.embeddings import LiteLLMEmbeddingProvider
        assert LiteLLMEmbeddingProvider is not None
    except ImportError:
        pytest.fail("Failed to import LiteLLMEmbeddingProvider")


def test_litellm_embedding_provider_initialization():
    """Test LiteLLMEmbeddingProvider initialization."""
    from jarvis.llm.embeddings import LiteLLMEmbeddingProvider
    
    provider = LiteLLMEmbeddingProvider(
        model="text-embedding-ada-002",
        api_key="test_key",
        dim=1536
    )
    
    assert provider.model == "text-embedding-ada-002"
    assert provider.api_key == "test_key"
    assert provider._dim == 1536


def test_litellm_embedding_provider_dimension_property():
    """Test LiteLLMEmbeddingProvider dimension property."""
    from jarvis.llm.embeddings import LiteLLMEmbeddingProvider
    
    provider = LiteLLMEmbeddingProvider(
        model="text-embedding-ada-002",
        api_key="test_key",
        dim=1536
    )
    
    assert provider.dimension == 1536


def test_litellm_embedding_provider_encode():
    """Test LiteLLMEmbeddingProvider encode method."""
    with patch('jarvis.llm.embeddings.litellm') as mock_litellm:
        mock_response = {
            "data": [
                {"embedding": [0.1, 0.2, 0.3]}
            ]
        }
        mock_litellm.embedding.return_value = mock_response
        
        from jarvis.llm.embeddings import LiteLLMEmbeddingProvider
        
        provider = LiteLLMEmbeddingProvider(
            model="text-embedding-ada-002",
            api_key="test_key",
            dim=1536
        )
        
        # Test encoding
        result = provider.encode("test text")
        
        assert result == [0.1, 0.2, 0.3]
        mock_litellm.embedding.assert_called_once_with(
            model="text-embedding-ada-002",
            input=["test text"],
            api_key="test_key"
        )


def test_litellm_embedding_provider_encode_no_api_key():
    """Test LiteLLMEmbeddingProvider encode without API key."""
    with patch('jarvis.llm.embeddings.litellm') as mock_litellm:
        mock_response = {
            "data": [
                {"embedding": [0.1, 0.2, 0.3]}
            ]
        }
        mock_litellm.embedding.return_value = mock_response
        
        from jarvis.llm.embeddings import LiteLLMEmbeddingProvider
        
        provider = LiteLLMEmbeddingProvider(
            model="text-embedding-ada-002",
            api_key=None,
            dim=1536
        )
        
        # Test encoding
        result = provider.encode("test text")
        
        assert result == [0.1, 0.2, 0.3]
        mock_litellm.embedding.assert_called_once_with(
            model="text-embedding-ada-002",
            input=["test text"]
        )


def test_get_embedding_provider_import():
    """Test that get_embedding_provider function imports correctly."""
    try:
        from jarvis.llm.embeddings import get_embedding_provider
        assert get_embedding_provider is not None
    except ImportError:
        pytest.fail("Failed to import get_embedding_provider")


def test_get_embedding_provider_default():
    """Test get_embedding_provider with default settings."""
    with patch('jarvis.llm.embeddings.get_settings') as mock_get_settings:
        mock_settings = Mock()
        mock_settings.embedding_provider = "unknown"
        mock_settings.vector_dim = 768
        mock_get_settings.return_value = mock_settings
        
        from jarvis.llm.embeddings import get_embedding_provider, MockEmbeddingProvider
        
        provider = get_embedding_provider()
        
        assert isinstance(provider, MockEmbeddingProvider)
        assert provider.dimension == 768


def test_get_embedding_provider_with_settings():
    """Test get_embedding_provider with custom settings."""
    mock_settings = Mock()
    mock_settings.embedding_provider = "unknown"
    mock_settings.vector_dim = 512
    
    from jarvis.llm.embeddings import get_embedding_provider, MockEmbeddingProvider
    
    provider = get_embedding_provider(mock_settings)
    
    assert isinstance(provider, MockEmbeddingProvider)
    assert provider.dimension == 512


def test_get_embedding_provider_sentence_transformers():
    """Test get_embedding_provider with sentence-transformers."""
    with patch('jarvis.llm.embeddings.get_settings') as mock_get_settings:
        mock_settings = Mock()
        mock_settings.embedding_provider = "sentence-transformers"
        mock_settings.embedding_model = "all-MiniLM-L6-v2"
        mock_settings.embedding_device = "cpu"
        mock_settings.vector_dim = 384
        mock_settings.embedding_fallback_to_mock = False
        mock_get_settings.return_value = mock_settings
        
        from jarvis.llm.embeddings import get_embedding_provider, SentenceTransformerProvider
        
        provider = get_embedding_provider()
        
        assert isinstance(provider, SentenceTransformerProvider)
        assert provider.model_name == "all-MiniLM-L6-v2"
        assert provider.device == "cpu"
        assert provider._dim == 384


def test_get_embedding_provider_sentence_transformers_fallback():
    """Test get_embedding_provider with sentence-transformers fallback."""
    with patch('jarvis.llm.embeddings.get_settings') as mock_get_settings:
        mock_settings = Mock()
        mock_settings.embedding_provider = "sentence-transformers"
        mock_settings.embedding_model = "invalid-model"
        mock_settings.embedding_device = "cpu"
        mock_settings.vector_dim = 384
        mock_settings.embedding_fallback_to_mock = True
        mock_get_settings.return_value = mock_settings
        
        from jarvis.llm.embeddings import get_embedding_provider, MockEmbeddingProvider
        
        provider = get_embedding_provider()
        
        assert isinstance(provider, MockEmbeddingProvider)
        assert provider.dimension == 384


def test_get_embedding_provider_sentence_transformers_no_fallback():
    """Test get_embedding_provider with sentence-transformers no fallback."""
    with patch('jarvis.llm.embeddings.get_settings') as mock_get_settings:
        mock_settings = Mock()
        mock_settings.embedding_provider = "sentence-transformers"
        mock_settings.embedding_model = "invalid-model"
        mock_settings.embedding_device = "cpu"
        mock_settings.vector_dim = 384
        mock_settings.embedding_fallback_to_mock = False
        mock_get_settings.return_value = mock_settings
        
        from jarvis.llm.embeddings import get_embedding_provider
        
        # Should raise RuntimeError
        with pytest.raises(RuntimeError, match="Could not load sentence-transformers model"):
            get_embedding_provider()


def test_get_embedding_provider_litellm():
    """Test get_embedding_provider with litellm."""
    with patch('jarvis.llm.embeddings.get_settings') as mock_get_settings:
        mock_settings = Mock()
        mock_settings.embedding_provider = "litellm"
        mock_settings.embedding_model = "text-embedding-ada-002"
        mock_settings.vector_dim = 1536
        mock_get_settings.return_value = mock_settings
        
        with patch('jarvis.llm.embeddings.get_secret') as mock_get_secret:
            mock_get_secret.return_value = "test_api_key"
            
            from jarvis.llm.embeddings import get_embedding_provider, LiteLLMEmbeddingProvider
            
            provider = get_embedding_provider()
            
            assert isinstance(provider, LiteLLMEmbeddingProvider)
            assert provider.model == "text-embedding-ada-002"
            assert provider.api_key == "test_api_key"
            assert provider._dim == 1536
            
            mock_get_secret.assert_called_once_with("litellm_api_key", env_override="LITELLM_API_KEY")


def test_get_embedding_provider_litellm_no_secret():
    """Test get_embedding_provider with litellm but no secret."""
    with patch('jarvis.llm.embeddings.get_settings') as mock_get_settings:
        mock_settings = Mock()
        mock_settings.embedding_provider = "litellm"
        mock_settings.embedding_model = "text-embedding-ada-002"
        mock_settings.vector_dim = 1536
        mock_get_settings.return_value = mock_settings
        
        with patch('jarvis.llm.embeddings.get_secret') as mock_get_secret:
            mock_get_secret.return_value = None
            
            from jarvis.llm.embeddings import get_embedding_provider, LiteLLMEmbeddingProvider
            
            provider = get_embedding_provider()
            
            assert isinstance(provider, LiteLLMEmbeddingProvider)
            assert provider.model == "text-embedding-ada-002"
            assert provider.api_key is None
            assert provider._dim == 1536


def test_sentence_transformer_provider_model_caching():
    """Test SentenceTransformerProvider model caching."""
    with patch('jarvis.llm.embeddings.SentenceTransformer') as mock_st:
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_st.return_value = mock_model
        
        from jarvis.llm.embeddings import SentenceTransformerProvider
        
        provider = SentenceTransformerProvider(
            model_name="all-MiniLM-L6-v2",
            device="cpu",
            dim=384
        )
        
        # Test model loading
        model1 = provider._load_model()
        model2 = provider._load_model()
        
        # Should only create model once
        assert model1 == model2
        assert mock_st.call_count == 1


def test_sentence_transformer_provider_dimension_after_loading():
    """Test SentenceTransformerProvider dimension after model loading."""
    with patch('jarvis.llm.embeddings.SentenceTransformer') as mock_st:
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 512
        mock_st.return_value = mock_model
        
        from jarvis.llm.embeddings import SentenceTransformerProvider
        
        provider = SentenceTransformerProvider(
            model_name="all-MiniLM-L6-v2",
            device="cpu",
            dim=384  # Initial dimension
        )
        
        # Access dimension property (should load model)
        dimension = provider.dimension
        
        assert dimension == 512  # Should be updated from model
        assert provider._dim == 512


def test_mock_embedding_provider_different_dimensions():
    """Test MockEmbeddingProvider with different dimensions."""
    from jarvis.llm.embeddings import MockEmbeddingProvider
    
    dimensions = [1, 10, 100, 768, 1024]
    
    for dim in dimensions:
        provider = MockEmbeddingProvider(dim=dim)
        result = provider.encode("test")
        
        assert len(result) == dim
        assert all(isinstance(x, float) for x in result)
        assert all(-1.0 <= x <= 1.0 for x in result)
