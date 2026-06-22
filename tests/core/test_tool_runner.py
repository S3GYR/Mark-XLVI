"""Tests for Tool Runner components."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
from typing import Any


def test_tool_runner_initialization():
    """Test tool runner initialization with proper configuration."""
    with patch('jarvis.core.tool_runner.Player') as mock_player:
        mock_player_instance = Mock()
        
        from jarvis.core.tool_runner import ToolRunner
        runner = ToolRunner(mock_player_instance)
        
        assert runner is not None
        assert runner.player == mock_player_instance


def test_tool_runner_tool_registration():
    """Test tool registration and discovery."""
    with patch('jarvis.core.tool_runner.Player') as mock_player:
        mock_player_instance = Mock()
        
        from jarvis.core.tool_runner import ToolRunner, _LEGACY_ACTIONS
        
        runner = ToolRunner(mock_player_instance)
        
        # Check legacy actions are available
        assert isinstance(_LEGACY_ACTIONS, dict)
        assert len(_LEGACY_ACTIONS) > 0
        
        # Check for expected legacy tools
        expected_tools = ['weather_report', 'file_controller', 'reminder']
        for tool in expected_tools:
            assert tool in _LEGACY_ACTIONS


def test_tool_runner_tool_execution():
    """Test tool execution with proper validation."""
    with patch('jarvis.core.tool_runner.Player') as mock_player:
        mock_player_instance = Mock()
        
        from jarvis.core.tool_runner import ToolRunner
        
        runner = ToolRunner(mock_player_instance)
        
        # Mock tool execution
        async def test_execution():
            with patch('jarvis.tools.registry.get_tool_function') as mock_get_tool:
                mock_func = Mock()
                mock_get_tool.return_value = mock_func
                
                with patch.object(runner, '_call') as mock_call:
                    mock_call.return_value = "Tool executed successfully"
                    
                    result = await runner.run("open_app", {"app": "notepad"})
                    assert result == "Tool executed successfully"
                    mock_get_tool.assert_called_once_with("open_app")
                    mock_call.assert_called_once()
        
        asyncio.run(test_execution())


def test_tool_runner_tool_validation():
    """Test tool parameter validation."""
    with patch('jarvis.core.tool_runner.get_settings'):
        from jarvis.core.tool_runner import ToolRunner
        
        runner = ToolRunner()
        
        # Test valid parameters
        valid_params = {"app": "notepad"}
        assert runner._validate_parameters("open_app", valid_params)
        
        # Test invalid parameters
        invalid_params = {"invalid_param": "value"}
        assert not runner._validate_parameters("open_app", invalid_params)


def test_tool_runner_error_handling():
    """Test error handling in tool execution."""
    with patch('jarvis.core.tool_runner.get_settings'):
        from jarvis.core.tool_runner import ToolRunner
        
        runner = ToolRunner()
        
        # Test tool not found
        result = runner.run_tool("nonexistent_tool", {})
        assert "error" in result.lower() or "not found" in result.lower()
        
        # Test tool execution error
        with patch.object(runner, '_execute_tool') as mock_execute:
            mock_execute.side_effect = Exception("Tool execution failed")
            
            result = runner.run_tool("open_app", {})
            assert "error" in result.lower()


def test_tool_runner_permission_checking():
    """Test permission checking for dangerous tools."""
    with patch('jarvis.core.tool_runner.get_settings'):
        from jarvis.core.tool_runner import ToolRunner
        
        runner = ToolRunner()
        
        # Test dangerous tool requiring permission
        with patch('jarvis.security.permissions.request_confirmation') as mock_confirm:
            mock_confirm.return_value = True
            
            result = runner.run_tool("computer_control", {"action": "click"})
            mock_confirm.assert_called()


def test_tool_runner_concurrent_execution():
    """Test concurrent tool execution capabilities."""
    with patch('jarvis.core.tool_runner.get_settings'):
        from jarvis.core.tool_runner import ToolRunner
        
        runner = ToolRunner()
        
        async def mock_tool_execution(tool_name, params):
            await asyncio.sleep(0.01)
            return f"executed_{tool_name}"
        
        # Test concurrent execution
        tools_to_run = [
            ("open_app", {"app": "notepad"}),
            ("desktop_control", {"code": "print('test')"}),
            ("send_message", {"message": "hello"})
        ]
        
        async def test_concurrent():
            with patch.object(runner, '_execute_tool_async', mock_tool_execution):
                results = await runner._run_concurrent(tools_to_run)
                
                assert len(results) == 3
                assert "executed_open_app" in results
                assert "executed_desktop_control" in results
                assert "executed_send_message" in results
        
        asyncio.run(test_concurrent())


def test_tool_runner_tool_timeout():
    """Test tool execution timeout handling."""
    with patch('jarvis.core.tool_runner.get_settings'):
        from jarvis.core.tool_runner import ToolRunner
        
        runner = ToolRunner()
        
        # Mock slow tool
        async def slow_tool(tool_name, params):
            await asyncio.sleep(2)  # Longer than timeout
            return "slow_result"
        
        async def test_timeout():
            with patch.object(runner, '_execute_tool_async', slow_tool):
                result = await runner._run_tool_with_timeout("slow_tool", {}, timeout=0.1)
                assert "timeout" in result.lower()
        
        asyncio.run(test_timeout())


def test_tool_runner_tool_cancellation():
    """Test tool execution cancellation."""
    with patch('jarvis.core.tool_runner.get_settings'):
        from jarvis.core.tool_runner import ToolRunner
        
        runner = ToolRunner()
        
        # Create cancellable task
        async def cancellable_tool(tool_name, params):
            await asyncio.sleep(1)
            return "completed"
        
        async def test_cancellation():
            task = asyncio.create_task(cancellable_tool("test", {}))
            
            # Cancel after short delay
            await asyncio.sleep(0.1)
            task.cancel()
            
            result = await runner._handle_cancellation(task)
            assert "cancelled" in result.lower()
        
        asyncio.run(test_cancellation())


def test_tool_runner_tool_dependency_injection():
    """Test dependency injection for tools."""
    with patch('jarvis.core.tool_runner.get_settings'):
        from jarvis.core.tool_runner import ToolRunner
        
        runner = ToolRunner()
        
        # Mock dependencies
        mock_memory = Mock()
        mock_player = Mock()
        
        runner._dependencies = {
            "memory": mock_memory,
            "player": mock_player
        }
        
        # Test tool gets dependencies
        with patch.object(runner, '_execute_tool') as mock_execute:
            mock_execute.return_value = "success"
            
            runner.run_tool("test_tool", {})
            
            # Check if dependencies were passed
            call_args = mock_execute.call_args
            assert call_args is not None


def test_tool_runner_tool_logging():
    """Test tool execution logging."""
    with patch('jarvis.core.tool_runner.get_settings'):
        from jarvis.core.tool_runner import ToolRunner
        
        runner = ToolRunner()
        
        with patch('jarvis.observability.logger.get_logger') as mock_logger:
            mock_logger_instance = Mock()
            mock_logger.return_value = mock_logger_instance
            
            with patch.object(runner, '_execute_tool') as mock_execute:
                mock_execute.return_value = "success"
                
                runner.run_tool("open_app", {"app": "notepad"})
                
                # Should log the execution
                mock_logger_instance.info.assert_called()


def test_tool_runner_tool_metrics():
    """Test tool execution metrics tracking."""
    with patch('jarvis.core.tool_runner.get_settings'):
        from jarvis.core.tool_runner import ToolRunner
        
        runner = ToolRunner()
        
        # Initial metrics
        metrics = runner.get_metrics()
        assert metrics["tools_executed"] == 0
        assert metrics["tools_failed"] == 0
        assert metrics["total_execution_time"] == 0
        
        # Execute tools
        with patch.object(runner, '_execute_tool') as mock_execute:
            mock_execute.return_value = "success"
            
            runner.run_tool("open_app", {})
            runner.run_tool("desktop_control", {})
            
            # Check metrics
            metrics = runner.get_metrics()
            assert metrics["tools_executed"] == 2
            assert metrics["tools_failed"] == 0


def test_tool_runner_tool_caching():
    """Test tool result caching."""
    with patch('jarvis.core.tool_runner.get_settings'):
        from jarvis.core.tool_runner import ToolRunner
        
        runner = ToolRunner()
        runner._enable_cache = True
        
        # First execution
        with patch.object(runner, '_execute_tool') as mock_execute:
            mock_execute.return_value = "cached_result"
            
            result1 = runner.run_tool("open_app", {"app": "notepad"})
            result2 = runner.run_tool("open_app", {"app": "notepad"})
            
            # Second call should use cache
            assert result1 == "cached_result"
            assert result2 == "cached_result"
            assert mock_execute.call_count == 1


def test_tool_runner_tool_sandbox_integration():
    """Test integration with security sandbox."""
    with patch('jarvis.core.tool_runner.get_settings'):
        from jarvis.core.tool_runner import ToolRunner
        
        runner = ToolRunner()
        
        with patch('jarvis.security.sandbox.Sandbox') as mock_sandbox:
            mock_sandbox_instance = Mock()
            mock_sandbox.return_value = mock_sandbox_instance
            mock_sandbox_instance.execute.return_value = "sandboxed_result"
            
            result = runner.run_tool("desktop_control", {"code": "print('test')"})
            
            mock_sandbox.assert_called_once()
            assert result == "sandboxed_result"


def test_tool_runner_tool_fallback_mechanism():
    """Test tool fallback mechanism for failures."""
    with patch('jarvis.core.tool_runner.get_settings'):
        from jarvis.core.tool_runner import ToolRunner
        
        runner = ToolRunner()
        
        # Primary tool fails
        with patch.object(runner, '_execute_tool') as mock_execute:
            mock_execute.side_effect = [Exception("Primary failed"), "fallback_success"]
            
            result = runner.run_tool_with_fallback("open_app", {"app": "notepad"}, "fallback_tool")
            assert result == "fallback_success"


def test_tool_runner_tool_state_management():
    """Test tool runner state management."""
    with patch('jarvis.core.tool_runner.get_settings'):
        from jarvis.core.tool_runner import ToolRunner
        
        runner = ToolRunner()
        
        # Initial state
        assert runner.get_state() == "idle"
        
        # Running state
        runner._running = True
        assert runner.get_state() == "running"
        
        # Error state
        runner._error = "Tool execution failed"
        assert runner.get_state() == "error"


def test_tool_runner_tool_cleanup():
    """Test proper cleanup of tool runner resources."""
    with patch('jarvis.core.tool_runner.get_settings'):
        from jarvis.core.tool_runner import ToolRunner
        
        runner = ToolRunner()
        
        # Set up some state
        runner._running = True
        runner._active_tasks = [Mock(), Mock()]
        
        # Cleanup
        runner.cleanup()
        
        assert not runner._running
        assert len(runner._active_tasks) == 0
