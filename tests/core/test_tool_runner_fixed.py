"""Fixed tests for Tool Runner components."""

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


def test_tool_runner_legacy_actions_available():
    """Test that legacy actions are properly registered."""
    from jarvis.core.tool_runner import _LEGACY_ACTIONS
    
    assert isinstance(_LEGACY_ACTIONS, dict)
    assert len(_LEGACY_ACTIONS) > 0
    
    # Check for expected legacy tools
    expected_tools = ['weather_report', 'file_controller', 'reminder']
    for tool in expected_tools:
        assert tool in _LEGACY_ACTIONS


def test_tool_runner_secure_tool_execution():
    """Test secure tool execution through registry."""
    with patch('jarvis.core.tool_runner.Player') as mock_player:
        mock_player_instance = Mock()
        
        from jarvis.core.tool_runner import ToolRunner
        
        runner = ToolRunner(mock_player_instance)
        
        async def test_secure_execution():
            with patch('jarvis.tools.registry.get_tool_function') as mock_get_tool:
                mock_func = AsyncMock()
                mock_func.return_value = "Secure tool executed"
                mock_get_tool.return_value = mock_func
                
                result = await runner.run("open_app", {"app": "notepad"})
                assert result == "Secure tool executed"
                mock_get_tool.assert_called_once_with("open_app")
                mock_func.assert_called_once_with({"app": "notepad"}, player=mock_player_instance)
        
        asyncio.run(test_secure_execution())


def test_tool_runner_legacy_tool_execution():
    """Test legacy tool execution fallback."""
    with patch('jarvis.core.tool_runner.Player') as mock_player:
        mock_player_instance = Mock()
        
        from jarvis.core.tool_runner import ToolRunner
        
        runner = ToolRunner(mock_player_instance)
        
        async def test_legacy_execution():
            with patch('jarvis.tools.registry.get_tool_function') as mock_get_tool:
                mock_get_tool.return_value = None  # No secure wrapper available
                
                with patch.object(runner, '_call_legacy') as mock_call_legacy:
                    mock_call_legacy.return_value = "Legacy tool executed"
                    
                    result = await runner.run("weather_report", {"location": "Paris"})
                    assert result == "Legacy tool executed"
                    mock_get_tool.assert_called_once_with("weather_report")
                    mock_call_legacy.assert_called_once()
        
        asyncio.run(test_legacy_execution())


def test_tool_runner_unknown_tool():
    """Test handling of unknown tools."""
    with patch('jarvis.core.tool_runner.Player') as mock_player:
        mock_player_instance = Mock()
        
        from jarvis.core.tool_runner import ToolRunner
        
        runner = ToolRunner(mock_player_instance)
        
        async def test_unknown_tool():
            with patch('jarvis.tools.registry.get_tool_function') as mock_get_tool:
                mock_get_tool.return_value = None  # No secure wrapper
                
                result = await runner.run("unknown_tool", {})
                assert result == "Unknown tool: unknown_tool"
        
        asyncio.run(test_unknown_tool())


def test_tool_runner_error_handling():
    """Test error handling in tool execution."""
    with patch('jarvis.core.tool_runner.Player') as mock_player:
        mock_player_instance = Mock()
        
        from jarvis.core.tool_runner import ToolRunner
        
        runner = ToolRunner(mock_player_instance)
        
        async def test_error_handling():
            with patch('jarvis.tools.registry.get_tool_function') as mock_get_tool:
                mock_func = AsyncMock()
                mock_func.side_effect = Exception("Tool execution failed")
                mock_get_tool.return_value = mock_func
                
                result = await runner.run("failing_tool", {})
                assert "Tool 'failing_tool' failed" in result
                assert "Tool execution failed" in result
        
        asyncio.run(test_error_handling())


def test_tool_runner_sync_function_call():
    """Test calling synchronous functions."""
    with patch('jarvis.core.tool_runner.Player') as mock_player:
        mock_player_instance = Mock()
        
        from jarvis.core.tool_runner import ToolRunner
        
        runner = ToolRunner(mock_player_instance)
        
        async def test_sync_call():
            sync_func = Mock()
            sync_func.return_value = "Sync result"
            
            result = await runner._call(sync_func, {"param": "value"})
            assert result == "Sync result"
            sync_func.assert_called_once_with({"param": "value"}, player=mock_player_instance)
        
        asyncio.run(test_sync_call())


def test_tool_runner_async_function_call():
    """Test calling asynchronous functions."""
    with patch('jarvis.core.tool_runner.Player') as mock_player:
        mock_player_instance = Mock()
        
        from jarvis.core.tool_runner import ToolRunner
        
        runner = ToolRunner(mock_player_instance)
        
        async def test_async_call():
            async_func = AsyncMock()
            async_func.return_value = "Async result"
            
            result = await runner._call(async_func, {"param": "value"})
            assert result == "Async result"
            async_func.assert_called_once_with({"param": "value"}, player=mock_player_instance)
        
        asyncio.run(test_async_call())


def test_tool_runner_legacy_sync_call():
    """Test calling legacy synchronous functions."""
    with patch('jarvis.core.tool_runner.Player') as mock_player:
        mock_player_instance = Mock()
        
        from jarvis.core.tool_runner import ToolRunner
        
        runner = ToolRunner(mock_player_instance)
        
        async def test_legacy_sync():
            legacy_func = Mock()
            legacy_func.return_value = "Legacy sync result"
            
            result = await runner._call_legacy(legacy_func, {"param": "value"})
            assert result == "Legacy sync result"
            legacy_func.assert_called_once_with(
                parameters={"param": "value"},
                player=mock_player_instance,
                response=None
            )
        
        asyncio.run(test_legacy_sync())


def test_tool_runner_legacy_async_call():
    """Test calling legacy asynchronous functions."""
    with patch('jarvis.core.tool_runner.Player') as mock_player:
        mock_player_instance = Mock()
        
        from jarvis.core.tool_runner import ToolRunner
        
        runner = ToolRunner(mock_player_instance)
        
        async def test_legacy_async():
            legacy_func = AsyncMock()
            legacy_func.return_value = "Legacy async result"
            
            result = await runner._call_legacy(legacy_func, {"param": "value"})
            assert result == "Legacy async result"
            legacy_func.assert_called_once_with(
                parameters={"param": "value"},
                player=mock_player_instance,
                response=None
            )
        
        asyncio.run(test_legacy_async())


def test_tool_runner_memory_save_handler():
    """Test the inline memory save handler."""
    with patch('jarvis.core.tool_runner.Player') as mock_player:
        mock_player_instance = Mock()
        
        from jarvis.core.tool_runner import ToolRunner
        
        runner = ToolRunner(mock_player_instance)
        
        async def test_memory_save():
            args = {"category": "notes", "key": "test", "value": "test value"}
            result = await runner.handle_memory_save(args)
            
            assert result["result"] == "ok"
            assert result["silent"] is True
        
        asyncio.run(test_memory_save())


def test_tool_runner_memory_save_handler_empty():
    """Test memory save handler with empty values."""
    with patch('jarvis.core.tool_runner.Player') as mock_player:
        mock_player_instance = Mock()
        
        from jarvis.core.tool_runner import ToolRunner
        
        runner = ToolRunner(mock_player_instance)
        
        async def test_memory_save_empty():
            args = {"category": "notes", "key": "", "value": ""}
            result = await runner.handle_memory_save(args)
            
            assert result["result"] == "ok"
            assert result["silent"] is True
        
        asyncio.run(test_memory_save_empty())


def test_tool_runner_null_result_handling():
    """Test handling of null results from tools."""
    with patch('jarvis.core.tool_runner.Player') as mock_player:
        mock_player_instance = Mock()
        
        from jarvis.core.tool_runner import ToolRunner
        
        runner = ToolRunner(mock_player_instance)
        
        async def test_null_result():
            with patch('jarvis.tools.registry.get_tool_function') as mock_get_tool:
                mock_func = AsyncMock()
                mock_func.return_value = None
                mock_get_tool.return_value = mock_func
                
                result = await runner.run("null_result_tool", {})
                assert result == "Done."
        
        asyncio.run(test_null_result())


def test_tool_runner_player_logging():
    """Test that player logging is called during tool execution."""
    with patch('jarvis.core.tool_runner.Player') as mock_player:
        mock_player_instance = Mock()
        mock_player_instance.write_log = Mock()
        
        from jarvis.core.tool_runner import ToolRunner
        
        runner = ToolRunner(mock_player_instance)
        
        async def test_logging():
            with patch('jarvis.tools.registry.get_tool_function') as mock_get_tool:
                mock_func = AsyncMock()
                mock_func.return_value = "Result"
                mock_get_tool.return_value = mock_func
                
                await runner.run("test_tool", {})
                
                mock_player_instance.write_log.assert_called_once_with("[tool] test_tool")
        
        asyncio.run(test_logging())
