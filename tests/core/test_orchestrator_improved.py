"""Improved tests for orchestrator module to increase coverage."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
from typing import Any


def test_orchestrator_import():
    """Test that orchestrator module imports correctly."""
    try:
        from jarvis.core.orchestrator import AgentOrchestrator
        assert AgentOrchestrator is not None
    except ImportError:
        pytest.fail("Failed to import AgentOrchestrator")


@pytest.mark.asyncio
async def test_orchestrator_initialization():
    """Test AgentOrchestrator initialization."""
    with patch('jarvis.core.orchestrator.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test_model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        
        mock_memory = AsyncMock()
        mock_player = Mock()
        
        from jarvis.core.orchestrator import AgentOrchestrator
        
        orchestrator = AgentOrchestrator(
            settings=mock_settings.return_value,
            memory=mock_memory,
            player=mock_player
        )
        
        assert orchestrator is not None
        assert orchestrator.settings == mock_settings.return_value
        assert orchestrator.memory == mock_memory
        assert orchestrator.player == mock_player


@pytest.mark.asyncio
async def test_orchestrator_run_basic():
    """Test AgentOrchestrator basic run functionality."""
    with patch('jarvis.core.orchestrator.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test_model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        
        mock_memory = AsyncMock()
        mock_player = Mock()
        
        with patch('jarvis.core.orchestrator.LLMClient') as mock_llm_client:
            mock_client = AsyncMock()
            mock_client.generate_response.return_value = "Test response"
            mock_llm_client.return_value = mock_client
            
            from jarvis.core.orchestrator import AgentOrchestrator
            
            orchestrator = AgentOrchestrator(
                settings=mock_settings.return_value,
                memory=mock_memory,
                player=mock_player
            )
            
            result = await orchestrator.run("Hello, JARVIS")
            
            assert result == "Test response"
            mock_client.generate_response.assert_called_once()


@pytest.mark.asyncio
async def test_orchestrator_run_with_memory():
    """Test AgentOrchestrator run with memory interaction."""
    with patch('jarvis.core.orchestrator.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test_model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        
        mock_memory = AsyncMock()
        mock_memory.search.return_value = [
            {"content": "Previous conversation", "metadata": {"source": "user"}}
        ]
        mock_player = Mock()
        
        with patch('jarvis.core.orchestrator.LLMClient') as mock_llm_client:
            mock_client = AsyncMock()
            mock_client.generate_response.return_value = "Contextual response"
            mock_llm_client.return_value = mock_client
            
            from jarvis.core.orchestrator import AgentOrchestrator
            
            orchestrator = AgentOrchestrator(
                settings=mock_settings.return_value,
                memory=mock_memory,
                player=mock_player
            )
            
            result = await orchestrator.run("Remember our conversation?")
            
            assert result == "Contextual response"
            mock_memory.search.assert_called_once()
            mock_client.generate_response.assert_called_once()


@pytest.mark.asyncio
async def test_orchestrator_error_handling():
    """Test AgentOrchestrator error handling."""
    with patch('jarvis.core.orchestrator.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test_model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        
        mock_memory = AsyncMock()
        mock_player = Mock()
        
        with patch('jarvis.core.orchestrator.LLMClient') as mock_llm_client:
            mock_client = AsyncMock()
            mock_client.generate_response.side_effect = Exception("LLM error")
            mock_llm_client.return_value = mock_client
            
            from jarvis.core.orchestrator import AgentOrchestrator
            
            orchestrator = AgentOrchestrator(
                settings=mock_settings.return_value,
                memory=mock_memory,
                player=mock_player
            )
            
            with pytest.raises(Exception, match="LLM error"):
                await orchestrator.run("Test input")


@pytest.mark.asyncio
async def test_orchestrator_memory_save():
    """Test AgentOrchestrator saves to memory."""
    with patch('jarvis.core.orchestrator.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test_model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        
        mock_memory = AsyncMock()
        mock_player = Mock()
        
        with patch('jarvis.core.orchestrator.LLMClient') as mock_llm_client:
            mock_client = AsyncMock()
            mock_client.generate_response.return_value = "Response to save"
            mock_llm_client.return_value = mock_client
            
            from jarvis.core.orchestrator import AgentOrchestrator
            
            orchestrator = AgentOrchestrator(
                settings=mock_settings.return_value,
                memory=mock_memory,
                player=mock_player
            )
            
            await orchestrator.run("Save this conversation")
            
            # Should save both user input and response
            assert mock_memory.save.call_count >= 2


@pytest.mark.asyncio
async def test_orchestrator_player_interaction():
    """Test AgentOrchestrator player interaction."""
    with patch('jarvis.core.orchestrator.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test_model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        
        mock_memory = AsyncMock()
        mock_player = Mock()
        
        with patch('jarvis.core.orchestrator.LLMClient') as mock_llm_client:
            mock_client = AsyncMock()
            mock_client.generate_response.return_value = "Audio response"
            mock_llm_client.return_value = mock_client
            
            from jarvis.core.orchestrator import AgentOrchestrator
            
            orchestrator = AgentOrchestrator(
                settings=mock_settings.return_value,
                memory=mock_memory,
                player=mock_player
            )
            
            await orchestrator.run("Speak to me")
            
            # Should call player for audio response
            mock_player.play.assert_called_once_with("Audio response")


@pytest.mark.asyncio
async def test_orchestrator_empty_input():
    """Test AgentOrchestrator handles empty input."""
    with patch('jarvis.core.orchestrator.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test_model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        
        mock_memory = AsyncMock()
        mock_player = Mock()
        
        from jarvis.core.orchestrator import AgentOrchestrator
        
        orchestrator = AgentOrchestrator(
            settings=mock_settings.return_value,
            memory=mock_memory,
            player=mock_player
        )
        
        # Test empty string
        result = await orchestrator.run("")
        assert result is not None
        
        # Test whitespace only
        result = await orchestrator.run("   ")
        assert result is not None


@pytest.mark.asyncio
async def test_orchestrator_long_input():
    """Test AgentOrchestrator handles long input."""
    with patch('jarvis.core.orchestrator.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test_model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        
        mock_memory = AsyncMock()
        mock_player = Mock()
        
        with patch('jarvis.core.orchestrator.LLMClient') as mock_llm_client:
            mock_client = AsyncMock()
            mock_client.generate_response.return_value = "Long input response"
            mock_llm_client.return_value = mock_client
            
            from jarvis.core.orchestrator import AgentOrchestrator
            
            orchestrator = AgentOrchestrator(
                settings=mock_settings.return_value,
                memory=mock_memory,
                player=mock_player
            )
            
            long_input = "This is a very long input " * 100
            result = await orchestrator.run(long_input)
            
            assert result == "Long input response"
            mock_client.generate_response.assert_called_once()


@pytest.mark.asyncio
async def test_orchestrator_concurrent_requests():
    """Test AgentOrchestrator handles concurrent requests."""
    with patch('jarvis.core.orchestrator.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test_model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        
        mock_memory = AsyncMock()
        mock_player = Mock()
        
        with patch('jarvis.core.orchestrator.LLMClient') as mock_llm_client:
            mock_client = AsyncMock()
            mock_client.generate_response.return_value = "Concurrent response"
            mock_llm_client.return_value = mock_client
            
            from jarvis.core.orchestrator import AgentOrchestrator
            
            orchestrator = AgentOrchestrator(
                settings=mock_settings.return_value,
                memory=mock_memory,
                player=mock_player
            )
            
            # Run multiple requests concurrently
            tasks = [
                orchestrator.run(f"Request {i}")
                for i in range(5)
            ]
            
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 5
            assert all(result == "Concurrent response" for result in results)


@pytest.mark.asyncio
async def test_orchestrator_memory_search_error():
    """Test AgentOrchestrator handles memory search errors."""
    with patch('jarvis.core.orchestrator.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test_model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        
        mock_memory = AsyncMock()
        mock_memory.search.side_effect = Exception("Memory search error")
        mock_player = Mock()
        
        with patch('jarvis.core.orchestrator.LLMClient') as mock_llm_client:
            mock_client = AsyncMock()
            mock_client.generate_response.return_value = "Response without memory"
            mock_llm_client.return_value = mock_client
            
            from jarvis.core.orchestrator import AgentOrchestrator
            
            orchestrator = AgentOrchestrator(
                settings=mock_settings.return_value,
                memory=mock_memory,
                player=mock_player
            )
            
            # Should handle memory search error gracefully
            result = await orchestrator.run("Test input")
            assert result == "Response without memory"


@pytest.mark.asyncio
async def test_orchestrator_memory_save_error():
    """Test AgentOrchestrator handles memory save errors."""
    with patch('jarvis.core.orchestrator.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test_model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        
        mock_memory = AsyncMock()
        mock_memory.save.side_effect = Exception("Memory save error")
        mock_player = Mock()
        
        with patch('jarvis.core.orchestrator.LLMClient') as mock_llm_client:
            mock_client = AsyncMock()
            mock_client.generate_response.return_value = "Response"
            mock_llm_client.return_value = mock_client
            
            from jarvis.core.orchestrator import AgentOrchestrator
            
            orchestrator = AgentOrchestrator(
                settings=mock_settings.return_value,
                memory=mock_memory,
                player=mock_player
            )
            
            # Should handle memory save error gracefully
            result = await orchestrator.run("Test input")
            assert result == "Response"


@pytest.mark.asyncio
async def test_orchestrator_player_error():
    """Test AgentOrchestrator handles player errors."""
    with patch('jarvis.core.orchestrator.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test_model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        
        mock_memory = AsyncMock()
        mock_player = Mock()
        mock_player.play.side_effect = Exception("Player error")
        
        with patch('jarvis.core.orchestrator.LLMClient') as mock_llm_client:
            mock_client = AsyncMock()
            mock_client.generate_response.return_value = "Audio response"
            mock_llm_client.return_value = mock_client
            
            from jarvis.core.orchestrator import AgentOrchestrator
            
            orchestrator = AgentOrchestrator(
                settings=mock_settings.return_value,
                memory=mock_memory,
                player=mock_player
            )
            
            # Should handle player error gracefully
            result = await orchestrator.run("Speak to me")
            assert result == "Audio response"


@pytest.mark.asyncio
async def test_orchestrator_special_characters():
    """Test AgentOrchestrator handles special characters."""
    with patch('jarvis.core.orchestrator.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test_model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        
        mock_memory = AsyncMock()
        mock_player = Mock()
        
        with patch('jarvis.core.orchestrator.LLMClient') as mock_llm_client:
            mock_client = AsyncMock()
            mock_client.generate_response.return_value = "Special chars response"
            mock_llm_client.return_value = mock_client
            
            from jarvis.core.orchestrator import AgentOrchestrator
            
            orchestrator = AgentOrchestrator(
                settings=mock_settings.return_value,
                memory=mock_memory,
                player=mock_player
            )
            
            special_input = "Test with émojis 🎉 and special chars: @#$%^&*()"
            result = await orchestrator.run(special_input)
            
            assert result == "Special chars response"
            mock_client.generate_response.assert_called_once()


@pytest.mark.asyncio
async def test_orchestrator_temperature_setting():
    """Test AgentOrchestrator respects temperature setting."""
    with patch('jarvis.core.orchestrator.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test_model"
        mock_settings.return_value.llm_temperature = 0.1  # Low temperature
        mock_settings.return_value.llm_max_tokens = 1000
        
        mock_memory = AsyncMock()
        mock_player = Mock()
        
        with patch('jarvis.core.orchestrator.LLMClient') as mock_llm_client:
            mock_client = AsyncMock()
            mock_client.generate_response.return_value = "Conservative response"
            mock_llm_client.return_value = mock_client
            
            from jarvis.core.orchestrator import AgentOrchestrator
            
            orchestrator = AgentOrchestrator(
                settings=mock_settings.return_value,
                memory=mock_memory,
                player=mock_player
            )
            
            await orchestrator.run("Test input")
            
            # Check that LLM client was created with correct temperature
            mock_llm_client.assert_called_once()
            call_kwargs = mock_llm_client.call_args[1]
            assert call_kwargs.get('temperature') == 0.1


@pytest.mark.asyncio
async def test_orchestrator_max_tokens_setting():
    """Test AgentOrchestrator respects max_tokens setting."""
    with patch('jarvis.core.orchestrator.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test_model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 500  # Limited tokens
        
        mock_memory = AsyncMock()
        mock_player = Mock()
        
        with patch('jarvis.core.orchestrator.LLMClient') as mock_llm_client:
            mock_client = AsyncMock()
            mock_client.generate_response.return_value = "Concise response"
            mock_llm_client.return_value = mock_client
            
            from jarvis.core.orchestrator import AgentOrchestrator
            
            orchestrator = AgentOrchestrator(
                settings=mock_settings.return_value,
                memory=mock_memory,
                player=mock_player
            )
            
            await orchestrator.run("Test input")
            
            # Check that LLM client was created with correct max_tokens
            mock_llm_client.assert_called_once()
            call_kwargs = mock_llm_client.call_args[1]
            assert call_kwargs.get('max_tokens') == 500
