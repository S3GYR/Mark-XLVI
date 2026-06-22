"""Real working tests for tool runner focusing on existing async API."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
from typing import Any


def test_tool_runner_import():
    """Test that tool runner imports correctly."""
    try:
        from jarvis.core.tool_runner import ToolRunner
        assert ToolRunner is not None
    except ImportError:
        pytest.fail("Failed to import ToolRunner")


def test_tool_runner_initialization():
    """Test tool runner initialization."""
    # Mock player
    mock_player = Mock()
    
    from jarvis.core.tool_runner import ToolRunner
    
    runner = ToolRunner(mock_player)
    
    assert runner is not None
    assert runner.player == mock_player


@pytest.mark.asyncio
async def test_tool_runner_run_secure_tool():
    """Test tool runner secure tool execution."""
    # Mock player
    mock_player = Mock()
    
    # Mock secure tool function
    async def mock_secure_tool(args: dict, player: Any) -> str:
        return f"secure_result_{args.get('param1', 'default')}_{args.get('param2', 0)}"
    
    with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_tool:
        mock_get_tool.return_value = mock_secure_tool
        
        from jarvis.core.tool_runner import ToolRunner
        
        runner = ToolRunner(mock_player)
        
        # Test secure tool execution
        result = await runner.run("test_secure_tool", {"param1": "test", "param2": 42})
        
        assert result == "secure_result_test_42"
        mock_player.write_log.assert_called_once_with("[tool] test_secure_tool")


@pytest.mark.asyncio
async def test_tool_runner_run_legacy_tool():
    """Test tool runner legacy tool execution."""
    # Mock player
    mock_player = Mock()
    
    # Mock legacy tool function
    async def mock_legacy_tool(parameters: dict, player: Any, response: Any) -> str:
        return f"legacy_result_{parameters.get('param1', 'default')}_{parameters.get('param2', 0)}"
    
    with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_tool:
        mock_get_tool.return_value = None  # No secure tool found
        
        # Mock legacy actions
        with patch('jarvis.core.tool_runner._LEGACY_ACTIONS', {"test_legacy_tool": mock_legacy_tool}):
            from jarvis.core.tool_runner import ToolRunner
            
            runner = ToolRunner(mock_player)
            
            # Test legacy tool execution
            result = await runner.run("test_legacy_tool", {"param1": "test", "param2": 42})
            
            assert result == "legacy_result_test_42"
            mock_player.write_log.assert_called_once_with("[tool] test_legacy_tool")


@pytest.mark.asyncio
async def test_tool_runner_run_unknown_tool():
    """Test tool runner unknown tool handling."""
    # Mock player
    mock_player = Mock()
    
    with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_tool:
        mock_get_tool.return_value = None  # No secure tool found
        
        # Mock empty legacy actions
        with patch('jarvis.core.tool_runner._LEGACY_ACTIONS', {}):
            from jarvis.core.tool_runner import ToolRunner
            
            runner = ToolRunner(mock_player)
            
            # Test unknown tool
            result = await runner.run("unknown_tool", {"param": "test"})
            
            assert result == "Unknown tool: unknown_tool"
            mock_player.write_log.assert_called_once_with("[tool] unknown_tool")


@pytest.mark.asyncio
async def test_tool_runner_run_tool_with_exception():
    """Test tool runner error handling."""
    # Mock player
    mock_player = Mock()
    
    # Mock tool that raises exception
    async def mock_failing_tool(args: dict, player: Any) -> str:
        raise ValueError("Tool failed")
    
    with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_tool:
        mock_get_tool.return_value = mock_failing_tool
        
        from jarvis.core.tool_runner import ToolRunner
        
        runner = ToolRunner(mock_player)
        
        # Test error handling
        result = await runner.run("failing_tool", {"param": "test"})
        
        assert "Tool 'failing_tool' failed" in result
        assert "Tool failed" in result
        mock_player.write_log.assert_called_once_with("[tool] failing_tool")


@pytest.mark.asyncio
async def test_tool_runner_sync_secure_tool():
    """Test tool runner with synchronous secure tool."""
    # Mock player
    mock_player = Mock()
    
    # Mock sync secure tool function
    def mock_sync_tool(args: dict, player: Any) -> str:
        return f"sync_result_{args.get('param', 'default')}"
    
    with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_tool:
        mock_get_tool.return_value = mock_sync_tool
        
        from jarvis.core.tool_runner import ToolRunner
        
        runner = ToolRunner(mock_player)
        
        # Test sync tool execution
        result = await runner.run("sync_tool", {"param": "test"})
        
        assert result == "sync_result_test"
        mock_player.write_log.assert_called_once_with("[tool] sync_tool")


@pytest.mark.asyncio
async def test_tool_runner_sync_legacy_tool():
    """Test tool runner with synchronous legacy tool."""
    # Mock player
    mock_player = Mock()
    
    # Mock sync legacy tool function
    def mock_sync_legacy_tool(parameters: dict, player: Any, response: Any) -> str:
        return f"sync_legacy_result_{parameters.get('param', 'default')}"
    
    with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_tool:
        mock_get_tool.return_value = None  # No secure tool found
        
        # Mock legacy actions
        with patch('jarvis.core.tool_runner._LEGACY_ACTIONS', {"sync_legacy_tool": mock_sync_legacy_tool}):
            from jarvis.core.tool_runner import ToolRunner
            
            runner = ToolRunner(mock_player)
            
            # Test sync legacy tool execution
            result = await runner.run("sync_legacy_tool", {"param": "test"})
            
            assert result == "sync_legacy_result_test"
            mock_player.write_log.assert_called_once_with("[tool] sync_legacy_tool")


@pytest.mark.asyncio
async def test_tool_runner_handle_memory_save():
    """Test tool runner memory save functionality."""
    # Mock player
    mock_player = Mock()
    
    from jarvis.core.tool_runner import ToolRunner
    
    runner = ToolRunner(mock_player)
    
    # Test memory save
    result = await runner.handle_memory_save({"category": "test", "key": "test_key", "value": "test_value"})
    
    assert result == {"result": "ok", "silent": True}


@pytest.mark.asyncio
async def test_tool_runner_handle_memory_save_minimal():
    """Test tool runner memory save with minimal parameters."""
    # Mock player
    mock_player = Mock()
    
    from jarvis.core.tool_runner import ToolRunner
    
    runner = ToolRunner(mock_player)
    
    # Test memory save with minimal parameters
    result = await runner.handle_memory_save({})
    
    assert result == {"result": "ok", "silent": True}


@pytest.mark.asyncio
async def test_tool_runner_concurrent_execution():
    """Test tool runner concurrent execution."""
    # Mock player
    mock_player = Mock()
    
    # Mock async tool function
    async def mock_async_tool(args: dict, player: Any) -> str:
        await asyncio.sleep(0.01)
        return f"async_result_{args.get('param', 'default')}"
    
    with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_tool:
        mock_get_tool.return_value = mock_async_tool
        
        from jarvis.core.tool_runner import ToolRunner
        
        runner = ToolRunner(mock_player)
        
        # Test concurrent execution
        tasks = []
        for i in range(3):
            task = asyncio.create_task(runner.run(f"async_tool_{i}", {"param": f"test_{i}"}))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result == f"async_result_test_{i}"


@pytest.mark.asyncio
async def test_tool_runner_parameter_validation():
    """Test tool runner parameter validation."""
    # Mock player
    mock_player = Mock()
    
    # Mock tool with specific parameters
    async def mock_validated_tool(args: dict, player: Any) -> str:
        required_param = args.get('required_param', '')
        optional_param = args.get('optional_param', 10)
        return f"validated_{required_param}_{optional_param}"
    
    with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_tool:
        mock_get_tool.return_value = mock_validated_tool
        
        from jarvis.core.tool_runner import ToolRunner
        
        runner = ToolRunner(mock_player)
        
        # Test with all parameters
        result = await runner.run("validated_tool", {"required_param": "test", "optional_param": 20})
        assert result == "validated_test_20"
        
        # Test with missing required parameter
        result = await runner.run("validated_tool", {"optional_param": 20})
        assert result == "validated__20"  # Tool handles missing params gracefully


@pytest.mark.asyncio
async def test_tool_runner_none_result():
    """Test tool runner with None result."""
    # Mock player
    mock_player = Mock()
    
    # Mock tool that returns None
    async def mock_none_tool(args: dict, player: Any) -> None:
        return None
    
    with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_tool:
        mock_get_tool.return_value = mock_none_tool
        
        from jarvis.core.tool_runner import ToolRunner
        
        runner = ToolRunner(mock_player)
        
        # Test None result handling
        result = await runner.run("none_tool", {"param": "test"})
        
        assert result == "Done."
        mock_player.write_log.assert_called_once_with("[tool] none_tool")


@pytest.mark.asyncio
async def test_tool_runner_empty_args():
    """Test tool runner with empty arguments."""
    # Mock player
    mock_player = Mock()
    
    # Mock tool that handles empty args
    async def mock_empty_args_tool(args: dict, player: Any) -> str:
        return f"empty_args_{len(args)}"
    
    with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_tool:
        mock_get_tool.return_value = mock_empty_args_tool
        
        from jarvis.core.tool_runner import ToolRunner
        
        runner = ToolRunner(mock_player)
        
        # Test empty arguments
        result = await runner.run("empty_args_tool", {})
        
        assert result == "empty_args_0"
        mock_player.write_log.assert_called_once_with("[tool] empty_args_tool")


@pytest.mark.asyncio
async def test_tool_runner_complex_args():
    """Test tool runner with complex arguments."""
    # Mock player
    mock_player = Mock()
    
    # Mock tool that handles complex args
    async def mock_complex_tool(args: dict, player: Any) -> str:
        nested = args.get('nested', {})
        return f"complex_{nested.get('key', 'default')}"
    
    with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_tool:
        mock_get_tool.return_value = mock_complex_tool
        
        from jarvis.core.tool_runner import ToolRunner
        
        runner = ToolRunner(mock_player)
        
        # Test complex arguments
        result = await runner.run("complex_tool", {"nested": {"key": "value"}})
        
        assert result == "complex_value"
        mock_player.write_log.assert_called_once_with("[tool] complex_tool")


@pytest.mark.asyncio
async def test_tool_runner_legacy_tool_with_response():
    """Test tool runner legacy tool with response parameter."""
    # Mock player
    mock_player = Mock()
    
    # Mock legacy tool that uses response parameter
    async def mock_response_tool(parameters: dict, player: Any, response: Any) -> str:
        return f"response_tool_{parameters.get('param', 'default')}_response_{response is not None}"
    
    with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_tool:
        mock_get_tool.return_value = None  # No secure tool found
        
        # Mock legacy actions
        with patch('jarvis.core.tool_runner._LEGACY_ACTIONS', {"response_tool": mock_response_tool}):
            from jarvis.core.tool_runner import ToolRunner
            
            runner = ToolRunner(mock_player)
            
            # Test legacy tool with response
            result = await runner.run("response_tool", {"param": "test"})
            
            assert result == "response_tool_test_response_False"
            mock_player.write_log.assert_called_once_with("[tool] response_tool")


@pytest.mark.asyncio
async def test_tool_runner_logging():
    """Test tool runner logging functionality."""
    # Mock player
    mock_player = Mock()
    
    # Mock tool
    async def mock_logging_tool(args: dict, player: Any) -> str:
        return "logged_result"
    
    with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_tool:
        mock_get_tool.return_value = mock_logging_tool
        
        from jarvis.core.tool_runner import ToolRunner
        
        runner = ToolRunner(mock_player)
        
        # Run a tool
        result = await runner.run("logging_tool", {"param": "test"})
        
        # Verify logging
        mock_player.write_log.assert_called_once_with("[tool] logging_tool")
        assert result == "logged_result"


@pytest.mark.asyncio
async def test_tool_runner_error_logging():
    """Test tool runner error logging."""
    # Mock player
    mock_player = Mock()
    
    # Mock tool that raises exception
    async def mock_error_tool(args: dict, player: Any) -> str:
        raise RuntimeError("Test error")
    
    with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_tool:
        mock_get_tool.return_value = mock_error_tool
        
        from jarvis.core.tool_runner import ToolRunner
        
        runner = ToolRunner(mock_player)
        
        # Run a tool that fails
        result = await runner.run("error_tool", {"param": "test"})
        
        # Verify error handling and logging
        assert "Tool 'error_tool' failed" in result
        assert "Test error" in result
        mock_player.write_log.assert_called_once_with("[tool] error_tool")


@pytest.mark.asyncio
async def test_tool_runner_tool_priority():
    """Test tool runner prefers secure tools over legacy tools."""
    # Mock player
    mock_player = Mock()
    
    # Mock secure tool
    async def mock_secure_tool(args: dict, player: Any) -> str:
        return "secure_result"
    
    # Mock legacy tool (should not be called)
    async def mock_legacy_tool(parameters: dict, player: Any, response: Any) -> str:
        return "legacy_result"
    
    with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_tool:
        mock_get_tool.return_value = mock_secure_tool
        
        # Mock legacy actions
        with patch('jarvis.core.tool_runner._LEGACY_ACTIONS', {"priority_tool": mock_legacy_tool}):
            from jarvis.core.tool_runner import ToolRunner
            
            runner = ToolRunner(mock_player)
            
            # Test that secure tool is preferred
            result = await runner.run("priority_tool", {"param": "test"})
            
            assert result == "secure_result"  # Should use secure tool
            mock_player.write_log.assert_called_once_with("[tool] priority_tool")
