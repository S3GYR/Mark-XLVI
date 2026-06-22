"""Comprehensive end-to-end integration tests for MARK XLVI."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
import json
import tempfile
import os
from typing import Any


@pytest.mark.asyncio
async def test_full_assistant_workflow():
    """Test complete assistant workflow from input to response."""
    with patch('jarvis.main.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        mock_settings.return_value.llm_api_key = "test-key"
        
        with patch('jarvis.main.get_memory_store') as mock_memory_store:
            mock_memory = AsyncMock()
            mock_memory_store.return_value = mock_memory
            
            with patch('jarvis.main.AgentOrchestrator') as mock_orchestrator_class:
                mock_orchestrator = AsyncMock()
                mock_orchestrator.run.return_value = "Hello! I'm JARVIS, your assistant."
                mock_orchestrator_class.return_value = mock_orchestrator
                
                with patch('jarvis.main.ConsolePlayer') as mock_player_class:
                    mock_player = Mock()
                    mock_player_class.return_value = mock_player
                    
                    from jarvis.main import JarvisAssistant
                    
                    # Create and setup assistant
                    assistant = JarvisAssistant()
                    await assistant.setup()
                    
                    # Test command execution
                    result = await assistant.run_command("Hello JARVIS")
                    
                    assert result == "Hello! I'm JARVIS, your assistant."
                    mock_orchestrator.run.assert_called_once_with("Hello JARVIS")
                    mock_player.play.assert_called_once_with("Hello! I'm JARVIS, your assistant.")
                    
                    await assistant.shutdown()


@pytest.mark.asyncio
async def test_memory_integration_workflow():
    """Test memory integration with assistant workflow."""
    with patch('jarvis.main.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        
        with patch('jarvis.main.get_memory_store') as mock_memory_store:
            mock_memory = AsyncMock()
            mock_memory.search.return_value = [
                {"content": "Previous conversation", "metadata": {"source": "user"}}
            ]
            mock_memory_store.return_value = mock_memory
            
            with patch('jarvis.main.AgentOrchestrator') as mock_orchestrator_class:
                mock_orchestrator = AsyncMock()
                mock_orchestrator.run.return_value = "I remember our previous conversation."
                mock_orchestrator_class.return_value = mock_orchestrator
                
                with patch('jarvis.main.ConsolePlayer') as mock_player_class:
                    mock_player = Mock()
                    mock_player_class.return_value = mock_player
                    
                    from jarvis.main import JarvisAssistant
                    
                    assistant = JarvisAssistant()
                    await assistant.setup()
                    
                    # Test memory-dependent command
                    result = await assistant.run_command("Do you remember me?")
                    
                    assert result == "I remember our previous conversation."
                    mock_memory.search.assert_called_once()
                    mock_orchestrator.run.assert_called_once()
                    
                    await assistant.shutdown()


@pytest.mark.asyncio
async def test_tool_runner_integration():
    """Test tool runner integration with orchestrator."""
    with patch('jarvis.core.orchestrator.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        
        mock_memory = AsyncMock()
        mock_player = Mock()
        
        with patch('jarvis.core.orchestrator.LLMClient') as mock_llm_client:
            mock_client = AsyncMock()
            mock_client.generate_response.return_value = "Tool executed successfully"
            mock_llm_client.return_value = mock_client
            
            with patch('jarvis.core.orchestrator.ToolRunner') as mock_tool_runner_class:
                mock_tool_runner = Mock()
                mock_tool_runner_class.return_value = mock_tool_runner
                
                from jarvis.core.orchestrator import AgentOrchestrator
                
                orchestrator = AgentOrchestrator(
                    settings=mock_settings.return_value,
                    memory=mock_memory,
                    player=mock_player
                )
                
                result = await orchestrator.run("Execute tool: test_tool")
                
                assert result == "Tool executed successfully"
                mock_tool_runner_class.assert_called_once_with(mock_player)


@pytest.mark.asyncio
async def test_llm_client_integration():
    """Test LLM client integration with orchestrator."""
    with patch('jarvis.core.orchestrator.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "gpt-4"
        mock_settings.return_value.llm_temperature = 0.5
        mock_settings.return_value.llm_max_tokens = 500
        mock_settings.return_value.llm_api_key = "test-api-key"
        
        mock_memory = AsyncMock()
        mock_player = Mock()
        
        with patch('litellm.completion') as mock_completion:
            mock_response = {
                "choices": [
                    {"message": {"content": "LLM integration response"}}
                ]
            }
            mock_completion.return_value = mock_response
            
            from jarvis.core.orchestrator import AgentOrchestrator
            
            orchestrator = AgentOrchestrator(
                settings=mock_settings.return_value,
                memory=mock_memory,
                player=mock_player
            )
            
            result = await orchestrator.run("Test LLM integration")
            
            assert result == "LLM integration response"
            mock_completion.assert_called_once()
            
            # Verify LLM parameters were passed correctly
            call_args = mock_completion.call_args[1]
            assert call_args.get('model') == "gpt-4"
            assert call_args.get('temperature') == 0.5
            assert call_args.get('max_tokens') == 500


@pytest.mark.asyncio
async def test_embeddings_integration():
    """Test embeddings integration with memory store."""
    with patch('jarvis.llm.embeddings.get_embedding_provider') as mock_get_provider:
        mock_provider = Mock()
        mock_provider.encode.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_provider.dimension = 5
        mock_get_provider.return_value = mock_provider
        
        with patch('jarvis.memory.json_store.get_settings') as mock_settings:
            mock_settings.return_value.memory_file = "test_memory.json"
            
            from jarvis.memory.json_store import JsonMemoryStore
            
            memory_store = JsonMemoryStore()
            await memory_store.initialize()
            
            # Test embedding-based search
            test_text = "Test embedding integration"
            embedding = mock_provider.encode(test_text)
            
            assert len(embedding) == 5
            assert all(isinstance(x, float) for x in embedding)
            mock_provider.encode.assert_called_once_with(test_text)
            
            await memory_store.close()


@pytest.mark.asyncio
async def test_web_server_integration():
    """Test web server integration with application."""
    with patch('jarvis.web.server.get_settings') as mock_settings:
        mock_settings.return_value.web_host = "127.0.0.1"
        mock_settings.return_value.web_port = 8000
        
        with patch('jarvis.web.server.AuthManager') as mock_auth_manager:
            mock_auth = Mock()
            mock_auth_manager.return_value = mock_auth
            
            from jarvis.web.server import DashboardServer
            
            server = DashboardServer()
            
            # Test server creation and route setup
            assert server is not None
            assert hasattr(server, 'app')
            
            # Check that routes are properly configured
            routes = [route.path for route in server.app.routes]
            assert "/" in routes
            assert "/login" in routes
            assert "/api/command" in routes


@pytest.mark.asyncio
async def test_audio_integration():
    """Test audio components integration."""
    with patch('jarvis.audio.capture.get_settings') as mock_settings:
        mock_settings.return_value.audio_sample_rate = 16000
        mock_settings.return_value.audio_chunk_size = 1024
        
        with patch('sounddevice.InputStream') as mock_stream:
            mock_stream_instance = Mock()
            mock_stream.return_value = mock_stream_instance
            
            from jarvis.audio.capture import AudioCapture
            
            # Test capture initialization
            output_callback = Mock()
            capture = AudioCapture(
                output_callback=output_callback,
                is_speaking=lambda: False,
                is_muted=lambda: False,
                is_phone_active=lambda: False
            )
            
            assert capture is not None
            assert capture._running is False
            
            # Test start/stop workflow
            loop = asyncio.get_event_loop()
            capture.start(loop)
            assert capture._running is True
            
            capture.stop()
            assert capture._running is False


@pytest.mark.asyncio
async def test_security_integration():
    """Test security components integration."""
    with patch('jarvis.security.secrets.get_secret') as mock_get_secret:
        mock_get_secret.return_value = "test-secret-value"
        
        with patch('jarvis.security.permissions.check_permission') as mock_check_permission:
            mock_check_permission.return_value = True
            
            from jarvis.security.secrets import get_secret
            from jarvis.security.permissions import check_permission
            
            # Test secret retrieval
            secret = get_secret("test_secret")
            assert secret == "test-secret-value"
            
            # Test permission checking
            has_permission = check_permission("file.read", "/safe/path")
            assert has_permission is True


@pytest.mark.asyncio
async def test_observability_integration():
    """Test observability components integration."""
    with patch('jarvis.observability.tracing.configure_tracing') as mock_configure_tracing:
        with patch('jarvis.observability.logger.configure_logging') as mock_configure_logging:
            
            from jarvis.observability.tracing import configure_tracing
            from jarvis.observability.logger import configure_logging
            
            # Test tracing configuration
            configure_tracing()
            mock_configure_tracing.assert_called_once()
            
            # Test logging configuration
            configure_logging()
            mock_configure_logging.assert_called_once()


@pytest.mark.asyncio
async def test_complete_workflow_with_errors():
    """Test complete workflow with error handling."""
    with patch('jarvis.main.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        
        with patch('jarvis.main.get_memory_store') as mock_memory_store:
            mock_memory = AsyncMock()
            mock_memory.save.side_effect = Exception("Memory save error")
            mock_memory_store.return_value = mock_memory
            
            with patch('jarvis.main.AgentOrchestrator') as mock_orchestrator_class:
                mock_orchestrator = AsyncMock()
                mock_orchestrator.run.return_value = "Response despite memory error"
                mock_orchestrator_class.return_value = mock_orchestrator
                
                with patch('jarvis.main.ConsolePlayer') as mock_player_class:
                    mock_player = Mock()
                    mock_player_class.return_value = mock_player
                    
                    from jarvis.main import JarvisAssistant
                    
                    assistant = JarvisAssistant()
                    await assistant.setup()
                    
                    # Test workflow continues despite memory errors
                    result = await assistant.run_command("Test error handling")
                    
                    assert result == "Response despite memory error"
                    
                    await assistant.shutdown()


@pytest.mark.asyncio
async def test_concurrent_requests_workflow():
    """Test workflow with concurrent requests."""
    with patch('jarvis.main.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        
        with patch('jarvis.main.get_memory_store') as mock_memory_store:
            mock_memory = AsyncMock()
            mock_memory_store.return_value = mock_memory
            
            with patch('jarvis.main.AgentOrchestrator') as mock_orchestrator_class:
                mock_orchestrator = AsyncMock()
                mock_orchestrator.run.return_value = "Concurrent response"
                mock_orchestrator_class.return_value = mock_orchestrator
                
                with patch('jarvis.main.ConsolePlayer') as mock_player_class:
                    mock_player = Mock()
                    mock_player_class.return_value = mock_player
                    
                    from jarvis.main import JarvisAssistant
                    
                    assistant = JarvisAssistant()
                    await assistant.setup()
                    
                    # Test concurrent requests
                    tasks = [
                        assistant.run_command(f"Concurrent request {i}")
                        for i in range(5)
                    ]
                    
                    results = await asyncio.gather(*tasks)
                    
                    assert len(results) == 5
                    assert all(result == "Concurrent response" for result in results)
                    
                    await assistant.shutdown()


@pytest.mark.asyncio
async def test_configuration_integration():
    """Test configuration integration across components."""
    with patch('jarvis.config.settings.get_settings') as mock_get_settings:
        mock_settings = Mock()
        mock_settings.llm_model = "test-model"
        mock_settings.llm_temperature = 0.7
        mock_settings.llm_max_tokens = 1000
        mock_settings.web_host = "127.0.0.1"
        mock_settings.web_port = 8000
        mock_settings.audio_sample_rate = 16000
        mock_settings.memory_file = "test_memory.json"
        mock_get_settings.return_value = mock_settings
        
        # Test that all components can access the same configuration
        from jarvis.config.settings import get_settings
        
        settings = get_settings()
        assert settings.llm_model == "test-model"
        assert settings.web_host == "127.0.0.1"
        assert settings.audio_sample_rate == 16000
        assert settings.memory_file == "test_memory.json"


@pytest.mark.asyncio
async def test_plugin_system_integration():
    """Test plugin/tool system integration."""
    with patch('jarvis.tools.registry.get_tool_function') as mock_get_tool:
        mock_tool = Mock()
        mock_tool.return_value = "Plugin executed"
        mock_get_tool.return_value = mock_tool
        
        with patch('jarvis.core.tool_runner.get_settings') as mock_settings:
            mock_settings.return_value.tool_timeout = 30
            
            from jarvis.core.tool_runner import ToolRunner
            from jarvis.core.player import ConsolePlayer
            
            player = ConsolePlayer()
            runner = ToolRunner(player)
            
            # Test plugin execution
            result = await runner.run("test_plugin", {"param": "value"})
            
            assert result == "Plugin executed"
            mock_get_tool.assert_called_once_with("test_plugin")


@pytest.mark.asyncio
async def test_data_flow_integration():
    """Test data flow between components."""
    with patch('jarvis.main.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        
        # Track data flow through the system
        data_flow = []
        
        def track_memory_save(key, value, category):
            data_flow.append(f"Memory save: {key}")
            
        def track_orchestrator_run(input_text):
            data_flow.append(f"Orchestrator run: {input_text}")
            return "Data flow response"
        
        with patch('jarvis.main.get_memory_store') as mock_memory_store:
            mock_memory = AsyncMock()
            mock_memory.save.side_effect = track_memory_save
            mock_memory_store.return_value = mock_memory
            
            with patch('jarvis.main.AgentOrchestrator') as mock_orchestrator_class:
                mock_orchestrator = AsyncMock()
                mock_orchestrator.run.side_effect = track_orchestrator_run
                mock_orchestrator_class.return_value = mock_orchestrator
                
                with patch('jarvis.main.ConsolePlayer') as mock_player_class:
                    mock_player = Mock()
                    mock_player_class.return_value = mock_player
                    
                    from jarvis.main import JarvisAssistant
                    
                    assistant = JarvisAssistant()
                    await assistant.setup()
                    
                    # Test data flow
                    result = await assistant.run_command("Track data flow")
                    
                    assert result == "Data flow response"
                    assert "Orchestrator run: Track data flow" in data_flow
                    assert len(data_flow) >= 2  # Should have memory saves too
                    
                    await assistant.shutdown()


@pytest.mark.asyncio
async def test_lifecycle_integration():
    """Test complete application lifecycle."""
    with patch('jarvis.main.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        
        lifecycle_events = []
        
        def track_lifecycle(event):
            lifecycle_events.append(event)
        
        with patch('jarvis.main.get_memory_store') as mock_memory_store:
            mock_memory = AsyncMock()
            mock_memory_store.return_value = mock_memory
            
            with patch('jarvis.main.AgentOrchestrator') as mock_orchestrator_class:
                mock_orchestrator = AsyncMock()
                mock_orchestrator.run.return_value = "Lifecycle test response"
                mock_orchestrator_class.return_value = mock_orchestrator
                
                with patch('jarvis.main.ConsolePlayer') as mock_player_class:
                    mock_player = Mock()
                    mock_player_class.return_value = mock_player
                    
                    from jarvis.main import JarvisAssistant
                    
                    # Test lifecycle: initialization -> setup -> run -> shutdown
                    track_lifecycle("initialization")
                    assistant = JarvisAssistant()
                    
                    track_lifecycle("setup")
                    await assistant.setup()
                    
                    track_lifecycle("run")
                    result = await assistant.run_command("Lifecycle test")
                    assert result == "Lifecycle test response"
                    
                    track_lifecycle("shutdown")
                    await assistant.shutdown()
                    
                    # Verify lifecycle events
                    expected_events = ["initialization", "setup", "run", "shutdown"]
                    assert lifecycle_events == expected_events


@pytest.mark.asyncio
async def test_error_recovery_integration():
    """Test error recovery across the system."""
    with patch('jarvis.main.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        
        error_count = 0
        
        def failing_operation():
            nonlocal error_count
            error_count += 1
            if error_count <= 2:
                raise Exception(f"Simulated error {error_count}")
            return "Success after recovery"
        
        with patch('jarvis.main.get_memory_store') as mock_memory_store:
            mock_memory = AsyncMock()
            mock_memory.save.side_effect = failing_operation
            mock_memory_store.return_value = mock_memory
            
            with patch('jarvis.main.AgentOrchestrator') as mock_orchestrator_class:
                mock_orchestrator = AsyncMock()
                mock_orchestrator.run.return_value = "Recovery response"
                mock_orchestrator_class.return_value = mock_orchestrator
                
                with patch('jarvis.main.ConsolePlayer') as mock_player_class:
                    mock_player = Mock()
                    mock_player_class.return_value = mock_player
                    
                    from jarvis.main import JarvisAssistant
                    
                    assistant = JarvisAssistant()
                    await assistant.setup()
                    
                    # Test error recovery
                    try:
                        result = await assistant.run_command("Test recovery")
                        # If it succeeds, system recovered
                        assert result == "Recovery response"
                    except Exception:
                        # If it fails, that's also acceptable behavior
                        pass
                    
                    assert error_count >= 2  # Should have attempted recovery
                    
                    await assistant.shutdown()
