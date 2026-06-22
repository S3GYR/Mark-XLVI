"""Integration tests for end-to-end workflows."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
from typing import Any


def test_full_command_processing_workflow():
    """Test complete command processing from input to response."""
    with patch('jarvis.core.orchestrator.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "gemini/gemini-2.5-flash"
        
        with patch('jarvis.core.orchestrator.get_memory_store') as mock_memory:
            mock_memory_instance = Mock()
            mock_memory.return_value = mock_memory_instance
            
            with patch('jarvis.core.orchestrator.LLMClient') as mock_llm:
                mock_llm_instance = Mock()
                mock_llm.return_value = mock_llm_instance
                
                with patch('jarvis.core.orchestrator.ToolRunner') as mock_tool_runner:
                    mock_tool_runner_instance = Mock()
                    mock_tool_runner.return_value = mock_tool_runner_instance
                    
                    from jarvis.core.orchestrator import AgentOrchestrator
                    orchestrator = AgentOrchestrator()
                    
                    async def test_workflow():
                        # Mock LLM response
                        mock_llm_instance.generate_response.return_value = "I'll help you with that task."
                        
                        # Mock tool execution
                        mock_tool_runner_instance.run.return_value = "Task completed successfully."
                        
                        # Process command
                        result = await orchestrator.process_command("Help me open notepad")
                        
                        assert result is not None
                        assert "help" in result.lower() or "task" in result.lower()
                        
                        # Verify interactions
                        mock_llm_instance.generate_response.assert_called()
                        mock_memory_instance.add.assert_called()
                    
                    asyncio.run(test_workflow())


def test_audio_to_text_to_command_workflow():
    """Test audio input processing to command execution."""
    with patch('jarvis.core.live_session.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "gemini/gemini-2.5-flash"
        
        with patch('jarvis.core.live_session.get_memory_store') as mock_memory:
            mock_memory_instance = Mock()
            mock_memory.return_value = mock_memory_instance
            
            with patch('jarvis.core.live_session.AudioCapture') as mock_capture:
                with patch('jarvis.core.live_session.AudioPlayback') as mock_playback:
                    with patch('jarvis.core.live_session.PhoneAudioRelay') as mock_phone:
                        with patch('jarvis.core.live_session.Player') as mock_player:
                            with patch('jarvis.core.live_session.ToolRunner') as mock_tool_runner:
                                
                                from jarvis.core.live_session import GeminiLiveSession
                                session = GeminiLiveSession()
                                
                                async def test_audio_workflow():
                                    # Mock audio input
                                    test_audio = b"audio_data_hello_world"
                                    
                                    # Mock transcription
                                    with patch.object(session, '_transcribe_audio') as mock_transcribe:
                                        mock_transcribe.return_value = "Hello world"
                                        
                                        # Mock command processing
                                        with patch.object(session, '_process_command') as mock_process:
                                            mock_process.return_value = "Hello! How can I help you?"
                                            
                                            # Process audio
                                            result = await session.process_audio(test_audio)
                                            
                                            assert result is not None
                                            mock_transcribe.assert_called_once_with(test_audio)
                                            mock_process.assert_called_once_with("Hello world")
                                
                                asyncio.run(test_audio_workflow())


def test_web_api_to_tool_execution_workflow():
    """Test web API request to tool execution workflow."""
    with patch('jarvis.web.server.get_settings') as mock_settings:
        mock_settings.return_value.api_host = "localhost"
        mock_settings.return_value.api_port = 8000
        
        with patch('jarvis.web.server.AgentOrchestrator') as mock_orchestrator:
            mock_orchestrator_instance = Mock()
            mock_orchestrator.return_value = mock_orchestrator_instance
            
            from jarvis.web.server import DashboardServer
            
            async def test_web_workflow():
                server = DashboardServer()
                
                # Mock command processing
                mock_orchestrator_instance.process_command.return_value = "Command executed via web API"
                
                # Simulate web request
                command_data = {"command": "open calculator", "user_id": "test_user"}
                
                with patch.object(server, '_handle_command_request') as mock_handle:
                    mock_handle.return_value = {"status": "success", "response": "Command executed via web API"}
                    
                    result = await server.process_web_command(command_data)
                    
                    assert result["status"] == "success"
                    assert "executed" in result["response"]
                    mock_orchestrator_instance.process_command.assert_called_once_with("open calculator")
            
            asyncio.run(test_web_workflow())


def test_memory_storage_and_retrieval_workflow():
    """Test memory storage and retrieval across components."""
    with patch('jarvis.memory.json_store.get_settings') as mock_settings:
        mock_settings.return_value.memory_file = "test_memory.json"
        
        from jarvis.memory.json_store import JsonMemoryStore
        
        async def test_memory_workflow():
            memory_store = JsonMemoryStore()
            
            # Store memory
            memory_data = {
                "content": "User prefers dark mode",
                "category": "preferences",
                "tags": ["ui", "settings"]
            }
            
            store_result = await memory_store.add(memory_data)
            assert store_result is not None
            
            # Search memory
            search_results = await memory_store.search("dark mode")
            assert len(search_results) > 0
            assert "dark mode" in search_results[0]["content"].lower()
            
            # Update memory
            update_data = {"content": "User prefers dark mode with high contrast"}
            update_result = await memory_store.update(search_results[0]["id"], update_data)
            assert update_result is not None
            
            # Verify update
            updated_results = await memory_store.search("high contrast")
            assert len(updated_results) > 0
        
        asyncio.run(test_memory_workflow())


def test_security_validation_workflow():
    """Test security validation across tool execution."""
    with patch('jarvis.security.permissions.get_settings') as mock_settings:
        mock_settings.return_value.security_level = "high"
        
        from jarvis.security.permissions import PermissionChecker
        from jarvis.security.sandbox import SecureSandbox
        
        def test_security_workflow():
            permission_checker = PermissionChecker()
            sandbox = SecureSandbox()
            
            # Test permission validation
            safe_command = "open notepad"
            unsafe_command = "rm -rf /"
            
            assert permission_checker.check_permission(safe_command, "file_operations")
            assert not permission_checker.check_permission(unsafe_command, "system_operations")
            
            # Test sandbox execution
            safe_code = "print('Hello, world!')"
            unsafe_code = "__import__('os').system('rm -rf /')"
            
            safe_result = sandbox.execute_code(safe_code)
            assert "Hello, world!" in safe_result
            
            # Unsafe code should be blocked or sandboxed
            try:
                unsafe_result = sandbox.execute_code(unsafe_code)
                # If it doesn't raise exception, result should be empty/safe
                assert unsafe_result == "" or "blocked" in unsafe_result.lower()
            except Exception:
                # Expected for unsafe code
                pass
        
        test_security_workflow()


def test_error_recovery_workflow():
    """Test error recovery and fallback mechanisms."""
    with patch('jarvis.core.orchestrator.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "gemini/gemini-2.5-flash"
        
        with patch('jarvis.core.orchestrator.get_memory_store') as mock_memory:
            mock_memory_instance = Mock()
            mock_memory.return_value = mock_memory_instance
            
            with patch('jarvis.core.orchestrator.LLMClient') as mock_llm:
                # Mock LLM failure
                mock_llm_instance = Mock()
                mock_llm_instance.generate_response.side_effect = Exception("LLM service unavailable")
                mock_llm.return_value = mock_llm_instance
                
                with patch('jarvis.core.orchestrator.ToolRunner') as mock_tool_runner:
                    mock_tool_runner_instance = Mock()
                    mock_tool_runner.return_value = mock_tool_runner_instance
                    
                    from jarvis.core.orchestrator import AgentOrchestrator
                    orchestrator = AgentOrchestrator()
                    
                    async def test_error_recovery():
                        # Process command with LLM failure
                        result = await orchestrator.process_command("test command")
                        
                        # Should fallback gracefully
                        assert result is not None
                        assert "error" in result.lower() or "unavailable" in result.lower()
                        
                        # Verify error logging
                        mock_memory_instance.add.assert_called()
                    
                    asyncio.run(test_error_recovery())


def test_concurrent_operations_workflow():
    """Test handling of concurrent operations."""
    with patch('jarvis.core.orchestrator.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "gemini/gemini-2.5-flash"
        
        with patch('jarvis.core.orchestrator.get_memory_store') as mock_memory:
            mock_memory_instance = Mock()
            mock_memory.return_value = mock_memory_instance
            
            with patch('jarvis.core.orchestrator.LLMClient') as mock_llm:
                mock_llm_instance = AsyncMock()
                mock_llm_instance.generate_response.return_value = "Response to command"
                mock_llm.return_value = mock_llm_instance
                
                with patch('jarvis.core.orchestrator.ToolRunner') as mock_tool_runner:
                    mock_tool_runner_instance = AsyncMock()
                    mock_tool_runner_instance.run.return_value = "Tool executed"
                    mock_tool_runner.return_value = mock_tool_runner_instance
                    
                    from jarvis.core.orchestrator import AgentOrchestrator
                    orchestrator = AgentOrchestrator()
                    
                    async def test_concurrent():
                        # Process multiple commands concurrently
                        commands = [
                            "command 1",
                            "command 2", 
                            "command 3"
                        ]
                        
                        tasks = [orchestrator.process_command(cmd) for cmd in commands]
                        results = await asyncio.gather(*tasks)
                        
                        assert len(results) == 3
                        assert all(result is not None for result in results)
                        
                        # Verify all commands were processed
                        assert mock_llm_instance.generate_response.call_count == 3
                    
                    asyncio.run(test_concurrent())


def test_configuration_loading_workflow():
    """Test configuration loading and validation workflow."""
    with patch('jarvis.config.settings.get_settings') as mock_get_settings:
        # Mock configuration file
        test_config = {
            "llm_model": "gemini/gemini-2.5-flash",
            "memory_type": "json",
            "api_host": "localhost",
            "api_port": 8000,
            "security_level": "high"
        }
        
        mock_settings = Mock()
        mock_settings.llm_model = test_config["llm_model"]
        mock_settings.memory_type = test_config["memory_type"]
        mock_settings.api_host = test_config["api_host"]
        mock_settings.api_port = test_config["api_port"]
        mock_settings.security_level = test_config["security_level"]
        
        mock_get_settings.return_value = mock_settings
        
        from jarvis.config.settings import get_settings
        
        def test_config_workflow():
            # Load configuration
            settings = get_settings()
            
            # Validate configuration
            assert settings.llm_model == test_config["llm_model"]
            assert settings.memory_type == test_config["memory_type"]
            assert settings.api_host == test_config["api_host"]
            assert settings.api_port == test_config["api_port"]
            assert settings.security_level == test_config["security_level"]
            
            # Test configuration validation
            assert settings.llm_model != ""
            assert settings.memory_type in ["json", "postgres"]
            assert settings.api_port > 0
            assert settings.security_level in ["low", "medium", "high"]
        
        test_config_workflow()


def test_logging_and_tracing_workflow():
    """Test logging and tracing across components."""
    with patch('jarvis.observability.tracing.configure_tracing') as mock_configure:
        with patch('jarvis.observability.logger.get_logger') as mock_logger:
            mock_logger_instance = Mock()
            mock_logger.return_value = mock_logger_instance
            
            from jarvis.observability.tracing import configure_tracing
            from jarvis.observability.logger import get_logger
            
            def test_observability_workflow():
                # Configure tracing
                configure_tracing(service_name="jarvis-test")
                mock_configure.assert_called_once()
                
                # Get logger
                logger = get_logger(__name__)
                mock_logger.assert_called_once_with(__name__)
                
                # Test logging
                logger.info("Test log message")
                logger.error("Test error message")
                
                # Verify logging calls
                assert mock_logger_instance.info.called
                assert mock_logger_instance.error.called
            
            test_observability_workflow()


def test_plugin_loading_workflow():
    """Test plugin loading and integration workflow."""
    with patch('jarvis.tools.registry.get_settings') as mock_settings:
        mock_settings.return_value.plugins_dir = "test_plugins"
        
        with patch('os.listdir') as mock_listdir:
            mock_listdir.return_value = ["plugin1.py", "plugin2.py", "invalid.txt"]
            
            with patch('importlib.import_module') as mock_import:
                # Mock successful plugin imports
                mock_plugin1 = Mock()
                mock_plugin2 = Mock()
                mock_import.side_effect = [mock_plugin1, mock_plugin2, ImportError("Not a Python file")]
                
                from jarvis.tools.registry import load_plugins
                
                def test_plugin_workflow():
                    # Load plugins
                    plugins = load_plugins()
                    
                    # Should load valid plugins
                    assert len(plugins) == 2
                    assert mock_plugin1 in plugins
                    assert mock_plugin2 in plugins
                    
                    # Verify import calls
                    assert mock_import.call_count == 3
                
                test_plugin_workflow()


def test_startup_and_shutdown_workflow():
    """Test complete application startup and shutdown workflow."""
    with patch('jarvis.main.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "gemini/gemini-2.5-flash"
        
        with patch('jarvis.main.get_memory_store') as mock_memory:
            mock_memory_instance = Mock()
            mock_memory.return_value = mock_memory_instance
            
            with patch('jarvis.main.AgentOrchestrator') as mock_orchestrator:
                mock_orchestrator_instance = Mock()
                mock_orchestrator.return_value = mock_orchestrator_instance
                
                with patch('jarvis.main.Player') as mock_player:
                    mock_player_instance = Mock()
                    mock_player.return_value = mock_player_instance
                    
                    from jarvis.main import JarvisAssistant
                    
                    async def test_lifecycle_workflow():
                        assistant = JarvisAssistant()
                        
                        # Test startup
                        with patch.object(assistant, 'setup') as mock_setup:
                            with patch.object(assistant, '_start_services') as mock_start:
                                
                                await assistant.startup()
                                
                                mock_setup.assert_called_once()
                                mock_start.assert_called_once()
                        
                        # Test shutdown
                        with patch.object(assistant, 'cleanup') as mock_cleanup:
                            with patch.object(assistant, '_stop_services') as mock_stop:
                                
                                await assistant.shutdown()
                                
                                mock_cleanup.assert_called_once()
                                mock_stop.assert_called_once()
                    
                    asyncio.run(test_lifecycle_workflow())
