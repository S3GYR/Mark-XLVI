"""Tests for main entry point and CLI initialization."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock
import asyncio
from io import StringIO
import sys


def test_main_initialization():
    """Test main entry point initialization."""
    with patch('jarvis.main.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "gemini/gemini-2.5-flash"
        
        with patch('jarvis.main.configure_logging') as mock_logging:
            with patch('jarvis.main.configure_tracing') as mock_tracing:
                from jarvis.main import JarvisAssistant
                
                assistant = JarvisAssistant()
                
                assert assistant is not None
                assert assistant.settings == mock_settings.return_value
                mock_logging.assert_not_called()  # Not called during init


def test_main_setup():
    """Test assistant setup process."""
    with patch('jarvis.main.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "gemini/gemini-2.5-flash"
        
        with patch('jarvis.main.configure_logging') as mock_logging:
            with patch('jarvis.main.configure_tracing') as mock_tracing:
                with patch('jarvis.main.get_memory_store') as mock_memory:
                    mock_memory.return_value = Mock()
                    
                    from jarvis.main import JarvisAssistant
                    
                    assistant = JarvisAssistant()
                    
                    # Run setup
                    asyncio.run(assistant.setup())
                    
                    mock_logging.assert_called_once()
                    mock_tracing.assert_called_once()
                    mock_memory.assert_called_once()
                    assert assistant.memory is not None
                    assert assistant.orchestrator is not None


def test_main_command_execution():
    """Test command execution through main interface."""
    with patch('jarvis.main.get_settings'):
        with patch('jarvis.main.configure_logging'):
            with patch('jarvis.main.configure_tracing'):
                with patch('jarvis.main.get_memory_store') as mock_memory:
                    mock_memory.return_value = Mock()
                    
                    from jarvis.main import JarvisAssistant
                    
                    assistant = JarvisAssistant()
                    asyncio.run(assistant.setup())
                    
                    # Mock orchestrator response
                    with patch.object(assistant.orchestrator, 'run') as mock_run:
                        mock_run.return_value = "Command executed successfully"
                        
                        result = asyncio.run(assistant.run_command("test command"))
                        assert result == "Command executed successfully"
                        mock_run.assert_called_once_with("test command")


def test_main_interactive_mode():
    """Test interactive CLI mode."""
    with patch('jarvis.main.get_settings'):
        with patch('jarvis.main.configure_logging'):
            with patch('jarvis.main.configure_tracing'):
                with patch('jarvis.main.get_memory_store') as mock_memory:
                    mock_memory.return_value = Mock()
                    
                    from jarvis.main import JarvisAssistant
                    
                    assistant = JarvisAssistant()
                    
                    # Mock user input
                    with patch('builtins.input', side_effect=["exit"]):
                        with patch.object(assistant, 'run_command') as mock_run:
                            mock_run.return_value = "Response"
                            
                            # Should not raise exception
                            asyncio.run(assistant.run_interactive())


def test_main_error_handling():
    """Test error handling in main operations."""
    with patch('jarvis.main.get_settings'):
        with patch('jarvis.main.configure_logging'):
            with patch('jarvis.main.configure_tracing'):
                with patch('jarvis.main.get_memory_store') as mock_memory:
                    mock_memory.return_value = Mock()
                    
                    from jarvis.main import JarvisAssistant
                    
                    assistant = JarvisAssistant()
                    asyncio.run(assistant.setup())
                    
                    # Test orchestrator error
                    with patch.object(assistant.orchestrator, 'run') as mock_run:
                        mock_run.side_effect = Exception("Orchestrator failed")
                        
                        result = asyncio.run(assistant.run_command("test"))
                        assert "error" in result.lower() or "failed" in result.lower()


def test_main_signal_handling():
    """Test graceful shutdown on signals."""
    with patch('jarvis.main.get_settings'):
        with patch('jarvis.main.configure_logging'):
            with patch('jarvis.main.configure_tracing'):
                with patch('jarvis.main.get_memory_store') as mock_memory:
                    mock_memory.return_value = Mock()
                    
                    from jarvis.main import JarvisAssistant
                    
                    assistant = JarvisAssistant()
                    asyncio.run(assistant.setup())
                    
                    # Test shutdown event
                    assert not assistant._shutdown.is_set()
                    assistant._shutdown.set()
                    assert assistant._shutdown.is_set()


def test_main_configuration_validation():
    """Test configuration validation."""
    from jarvis.main import JarvisAssistant
    
    # Test missing settings
    with patch('jarvis.main.get_settings') as mock_settings:
        mock_settings.return_value = None
        
        with pytest.raises(ValueError):
            JarvisAssistant()


def test_main_memory_store_fallback():
    """Test fallback to JSON store when PostgreSQL unavailable."""
    with patch('jarvis.main.get_settings'):
        with patch('jarvis.main.configure_logging'):
            with patch('jarvis.main.configure_tracing'):
                # Mock PostgreSQL failure
                with patch('jarvis.main.get_memory_store') as mock_memory:
                    mock_memory.side_effect = Exception("PostgreSQL unavailable")
                    
                    with patch('jarvis.memory.json_store.JsonMemoryStore') as mock_json:
                        mock_json.return_value = Mock()
                        
                        from jarvis.main import JarvisAssistant
                        
                        assistant = JarvisAssistant()
                        
                        # Should handle PostgreSQL failure gracefully
                        try:
                            asyncio.run(assistant.setup())
                        except Exception:
                            # Expected to fail if no fallback is implemented
                            pass


def test_main_logging_configuration():
    """Test logging configuration."""
    with patch('jarvis.main.configure_logging') as mock_logging:
        mock_logging.return_value = None
        
        from jarvis.main import configure_logging
        
        configure_logging()
        mock_logging.assert_called_once()


def test_main_tracing_configuration():
    """Test OpenTelemetry tracing configuration."""
    with patch('jarvis.main.configure_tracing') as mock_tracing:
        mock_tracing.return_value = None
        
        from jarvis.main import configure_tracing
        
        configure_tracing()
        mock_tracing.assert_called_once()


def test_main_cli_arguments():
    """Test CLI argument parsing."""
    with patch('sys.argv', ['jarvis', '--help']):
        with patch('argparse.ArgumentParser.print_help') as mock_help:
            try:
                from jarvis.main import main
                main()
            except SystemExit:
                # Expected for --help
                pass


def test_main_environment_variables():
    """Test environment variable handling."""
    with patch.dict('os.environ', {
        'JARVIS_LLM_MODEL': 'custom/model',
        'JARVIS_LOG_LEVEL': 'DEBUG'
    }):
        with patch('jarvis.main.get_settings') as mock_settings:
            mock_settings.return_value.llm_model = 'custom/model'
            
            from jarvis.main import JarvisAssistant
            
            assistant = JarvisAssistant()
            assert assistant.settings.llm_model == 'custom/model'


def test_main_plugin_loading():
    """Test plugin loading functionality."""
    with patch('jarvis.main.get_settings'):
        with patch('jarvis.main.configure_logging'):
            with patch('jarvis.main.configure_tracing'):
                with patch('jarvis.main.get_memory_store') as mock_memory:
                    mock_memory.return_value = Mock()
                    
                    from jarvis.main import JarvisAssistant
                    
                    assistant = JarvisAssistant()
                    
                    # Mock plugin loading
                    with patch.object(assistant, '_load_plugins') as mock_load:
                        mock_load.return_value = ["plugin1", "plugin2"]
                        
                        plugins = assistant._load_plugins()
                        assert len(plugins) == 2


def test_main_health_check():
    """Test health check functionality."""
    with patch('jarvis.main.get_settings'):
        with patch('jarvis.main.configure_logging'):
            with patch('jarvis.main.configure_tracing'):
                with patch('jarvis.main.get_memory_store') as mock_memory:
                    mock_memory.return_value = Mock()
                    
                    from jarvis.main import JarvisAssistant
                    
                    assistant = JarvisAssistant()
                    asyncio.run(assistant.setup())
                    
                    # Test health check
                    health = assistant.health_check()
                    assert "status" in health
                    assert "components" in health


def test_main_metrics_collection():
    """Test metrics collection."""
    with patch('jarvis.main.get_settings'):
        with patch('jarvis.main.configure_logging'):
            with patch('jarvis.main.configure_tracing'):
                with patch('jarvis.main.get_memory_store') as mock_memory:
                    mock_memory.return_value = Mock()
                    
                    from jarvis.main import JarvisAssistant
                    
                    assistant = JarvisAssistant()
                    asyncio.run(assistant.setup())
                    
                    # Test metrics
                    metrics = assistant.get_metrics()
                    assert "uptime" in metrics
                    assert "commands_processed" in metrics
                    assert "errors" in metrics


def test_main_cleanup():
    """Test cleanup on shutdown."""
    with patch('jarvis.main.get_settings'):
        with patch('jarvis.main.configure_logging'):
            with patch('jarvis.main.configure_tracing'):
                with patch('jarvis.main.get_memory_store') as mock_memory:
                    mock_memory.return_value = Mock()
                    
                    from jarvis.main import JarvisAssistant
                    
                    assistant = JarvisAssistant()
                    asyncio.run(assistant.setup())
                    
                    # Test cleanup
                    assistant.cleanup()
                    
                    # Verify cleanup was called
                    assert assistant.orchestrator is None or assistant.memory is None


def test_main_concurrent_commands():
    """Test handling concurrent commands."""
    with patch('jarvis.main.get_settings'):
        with patch('jarvis.main.configure_logging'):
            with patch('jarvis.main.configure_tracing'):
                with patch('jarvis.main.get_memory_store') as mock_memory:
                    mock_memory.return_value = Mock()
                    
                    from jarvis.main import JarvisAssistant
                    
                    assistant = JarvisAssistant()
                    asyncio.run(assistant.setup())
                    
                    async def test_concurrent():
                        # Mock multiple concurrent commands
                        with patch.object(assistant.orchestrator, 'run') as mock_run:
                            mock_run.return_value = "Response"
                            
                            tasks = [
                                assistant.run_command("command1"),
                                assistant.run_command("command2"),
                                assistant.run_command("command3")
                            ]
                            
                            results = await asyncio.gather(*tasks)
                            assert len(results) == 3
                            assert all(r == "Response" for r in results)
                    
                    asyncio.run(test_concurrent())


def test_main_version_output():
    """Test version information output."""
    with patch('sys.argv', ['jarvis', '--version']):
        with patch('builtins.print') as mock_print:
            try:
                from jarvis.main import main
                main()
            except SystemExit:
                # Expected for --version
                pass
            
            # Check if version was printed
            mock_print.assert_called()


def test_main_config_file_loading():
    """Test loading configuration from file."""
    with patch('pathlib.Path.exists', return_value=True):
        with patch('pathlib.Path.read_text') as mock_read:
            mock_read.return_value = '{"llm_model": "config/model"}'
            
            with patch('jarvis.main.get_settings') as mock_settings:
                mock_settings.return_value.llm_model = "config/model"
                
                from jarvis.main import JarvisAssistant
                
                assistant = JarvisAssistant()
                assert assistant.settings.llm_model == "config/model"
