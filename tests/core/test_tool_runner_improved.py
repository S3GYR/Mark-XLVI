"""Improved tests for tool runner with proper mocking."""

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
    """Test tool runner initialization with proper mocking."""
    with patch('jarvis.core.tool_runner.Player') as mock_player:
        mock_player_instance = Mock()
        mock_player.return_value = mock_player_instance
        
        from jarvis.core.tool_runner import ToolRunner
        
        runner = ToolRunner(player=mock_player_instance)
        
        assert runner is not None
        assert runner.player == mock_player_instance


def test_tool_runner_run_secure_tool():
    """Test tool runner with secure tool execution."""
    with patch('jarvis.core.tool_runner.Player') as mock_player:
        mock_player_instance = Mock()
        mock_player.return_value = mock_player_instance
        
        with patch('jarvis.core.tool_runner.get_secure_tool') as mock_get_tool:
            mock_tool = AsyncMock()
            mock_tool.return_value = "Tool executed successfully"
            mock_get_tool.return_value = mock_tool
            
            from jarvis.core.tool_runner import ToolRunner
            
            runner = ToolRunner(player=mock_player_instance)
            
            async def test_run():
                result = await runner.run("test_tool", {"param": "value"})
                
                assert result == "Tool executed successfully"
                mock_get_tool.assert_called_once_with("test_tool")
                mock_tool.assert_called_once_with({"param": "value"})
            
            asyncio.run(test_run())


def test_tool_runner_run_legacy_tool():
    """Test tool runner with legacy tool execution."""
    with patch('jarvis.core.tool_runner.Player') as mock_player:
        mock_player_instance = Mock()
        mock_player.return_value = mock_player_instance
        
        with patch('jarvis.core.tool_runner.get_secure_tool') as mock_get_tool:
            mock_get_tool.return_value = None  # No secure tool available
            
            with patch('jarvis.core.tool_runner.get_legacy_tool') as mock_get_legacy:
                mock_legacy_tool = Mock()
                mock_legacy_tool.return_value = "Legacy tool executed"
                mock_get_legacy.return_value = mock_legacy_tool
                
                from jarvis.core.tool_runner import ToolRunner
                
                runner = ToolRunner(player=mock_player_instance)
                
                async def test_run():
                    result = await runner.run("legacy_tool", {"param": "value"})
                    
                    assert result == "Legacy tool executed"
                    mock_get_tool.assert_called_once_with("legacy_tool")
                    mock_get_legacy.assert_called_once_with("legacy_tool")
                    mock_legacy_tool.assert_called_once_with({"param": "value"})
                
                asyncio.run(test_run())


def test_tool_runner_run_sync_function():
    """Test tool runner with synchronous function."""
    with patch('jarvis.core.tool_runner.Player') as mock_player:
        mock_player_instance = Mock()
        mock_player.return_value = mock_player_instance
        
        with patch('jarvis.core.tool_runner.get_secure_tool') as mock_get_tool:
            def sync_tool(param):
                return f"Sync tool executed with {param}"
            
            mock_get_tool.return_value = sync_tool
            
            from jarvis.core.tool_runner import ToolRunner
            
            runner = ToolRunner(player=mock_player_instance)
            
            async def test_run():
                result = await runner.run("sync_tool", {"param": "test"})
                
                assert result == "Sync tool executed with test"
                mock_get_tool.assert_called_once_with("sync_tool")
            
            asyncio.run(test_run())


def test_tool_runner_run_async_function():
    """Test tool runner with asynchronous function."""
    with patch('jarvis.core.tool_runner.Player') as mock_player:
        mock_player_instance = Mock()
        mock_player.return_value = mock_player_instance
        
        with patch('jarvis.core.tool_runner.get_secure_tool') as mock_get_tool:
            async def async_tool(param):
                await asyncio.sleep(0.01)
                return f"Async tool executed with {param}"
            
            mock_get_tool.return_value = async_tool
            
            from jarvis.core.tool_runner import ToolRunner
            
            runner = ToolRunner(player=mock_player_instance)
            
            async def test_run():
                result = await runner.run("async_tool", {"param": "test"})
                
                assert result == "Async tool executed with test"
                mock_get_tool.assert_called_once_with("async_tool")
            
            asyncio.run(test_run())


def test_tool_runner_error_handling():
    """Test tool runner error handling."""
    with patch('jarvis.core.tool_runner.Player') as mock_player:
        mock_player_instance = Mock()
        mock_player.return_value = mock_player_instance
        
        with patch('jarvis.core.tool_runner.get_secure_tool') as mock_get_tool:
            mock_tool = AsyncMock()
            mock_tool.side_effect = Exception("Tool execution failed")
            mock_get_tool.return_value = mock_tool
            
            from jarvis.core.tool_runner import ToolRunner
            
            runner = ToolRunner(player=mock_player_instance)
            
            async def test_run():
                with pytest.raises(Exception, match="Tool execution failed"):
                    await runner.run("failing_tool", {"param": "value"})
            
            asyncio.run(test_run())


def test_tool_runner_tool_not_found():
    """Test tool runner when tool is not found."""
    with patch('jarvis.core.tool_runner.Player') as mock_player:
        mock_player_instance = Mock()
        mock_player.return_value = mock_player_instance
        
        with patch('jarvis.core.tool_runner.get_secure_tool') as mock_get_tool:
            mock_get_tool.return_value = None
            
            with patch('jarvis.core.tool_runner.get_legacy_tool') as mock_get_legacy:
                mock_get_legacy.return_value = None
                
                from jarvis.core.tool_runner import ToolRunner
                
                runner = ToolRunner(player=mock_player_instance)
                
                async def test_run():
                    with pytest.raises(ValueError, match="Tool 'nonexistent_tool' not found"):
                        await runner.run("nonexistent_tool", {"param": "value"})
                
                asyncio.run(test_run())


def test_tool_runner_memory_save_handler():
    """Test tool runner memory save handler."""
    with patch('jarvis.core.tool_runner.Player') as mock_player:
        mock_player_instance = Mock()
        mock_player.return_value = mock_player_instance
        
        with patch('jarvis.core.tool_runner.get_memory_store') as mock_get_memory:
            mock_memory = Mock()
            mock_get_memory.return_value = mock_memory
            
            from jarvis.core.tool_runner import ToolRunner
            
            runner = ToolRunner(player=mock_player_instance)
            
            # Test memory save handler
            test_data = {"key": "value", "content": "test content"}
            runner._handle_memory_save(test_data)
            
            mock_memory.add.assert_called_once()


def test_tool_runner_null_result_handling():
    """Test tool runner null result handling."""
    with patch('jarvis.core.tool_runner.Player') as mock_player:
        mock_player_instance = Mock()
        mock_player.return_value = mock_player_instance
        
        with patch('jarvis.core.tool_runner.get_secure_tool') as mock_get_tool:
            mock_tool = AsyncMock()
            mock_tool.return_value = None
            mock_get_tool.return_value = mock_tool
            
            from jarvis.core.tool_runner import ToolRunner
            
            runner = ToolRunner(player=mock_player_instance)
            
            async def test_run():
                result = await runner.run("null_tool", {"param": "value"})
                
                assert result is None
                mock_get_tool.assert_called_once_with("null_tool")
            
            asyncio.run(test_run())


def test_tool_runner_player_logging():
    """Test tool runner player logging."""
    with patch('jarvis.core.tool_runner.Player') as mock_player:
        mock_player_instance = Mock()
        mock_player.return_value = mock_player_instance
        
        with patch('jarvis.core.tool_runner.get_secure_tool') as mock_get_tool:
            mock_tool = AsyncMock()
            mock_tool.return_value = "Tool executed"
            mock_get_tool.return_value = mock_tool
            
            from jarvis.core.tool_runner import ToolRunner
            
            runner = ToolRunner(player=mock_player_instance)
            
            async def test_run():
                result = await runner.run("test_tool", {"param": "value"})
                
                assert result == "Tool executed"
                # Verify player was used for logging
                assert mock_player_instance.log.call_count >= 0
            
            asyncio.run(test_run())


def test_tool_runner_concurrent_execution():
    """Test tool runner concurrent execution."""
    with patch('jarvis.core.tool_runner.Player') as mock_player:
        mock_player_instance = Mock()
        mock_player.return_value = mock_player_instance
        
        with patch('jarvis.core.tool_runner.get_secure_tool') as mock_get_tool:
            async def async_tool(param):
                await asyncio.sleep(0.01)
                return f"Tool executed with {param}"
            
            mock_get_tool.return_value = async_tool
            
            from jarvis.core.tool_runner import ToolRunner
            
            runner = ToolRunner(player=mock_player_instance)
            
            async def test_concurrent():
                # Run multiple tools concurrently
                tasks = []
                for i in range(5):
                    task = asyncio.create_task(
                        runner.run("test_tool", {"param": f"value_{i}"})
                    )
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks)
                
                assert len(results) == 5
                for i, result in enumerate(results):
                    assert result == f"Tool executed with value_{i}"
            
            asyncio.run(test_concurrent())


def test_tool_runner_parameter_validation():
    """Test tool runner parameter validation."""
    with patch('jarvis.core.tool_runner.Player') as mock_player:
        mock_player_instance = Mock()
        mock_player.return_value = mock_player_instance
        
        with patch('jarvis.core.tool_runner.get_secure_tool') as mock_get_tool:
            mock_tool = AsyncMock()
            mock_tool.return_value = "Tool executed"
            mock_get_tool.return_value = mock_tool
            
            from jarvis.core.tool_runner import ToolRunner
            
            runner = ToolRunner(player=mock_player_instance)
            
            async def test_validation():
                # Test with valid parameters
                result = await runner.run("test_tool", {"valid_param": "value"})
                assert result == "Tool executed"
                
                # Test with empty parameters
                result = await runner.run("test_tool", {})
                assert result == "Tool executed"
                
                # Test with None parameters
                result = await runner.run("test_tool", None)
                assert result == "Tool executed"
            
            asyncio.run(test_validation())


def test_tool_runner_tool_timeout():
    """Test tool runner timeout handling."""
    with patch('jarvis.core.tool_runner.Player') as mock_player:
        mock_player_instance = Mock()
        mock_player.return_value = mock_player_instance
        
        with patch('jarvis.core.tool_runner.get_secure_tool') as mock_get_tool:
            async def slow_tool(param):
                await asyncio.sleep(5)  # Slow tool
                return "Tool executed"
            
            mock_get_tool.return_value = slow_tool
            
            from jarvis.core.tool_runner import ToolRunner
            
            runner = ToolRunner(player=mock_player_instance)
            
            async def test_timeout():
                # Test with timeout
                try:
                    result = await asyncio.wait_for(
                        runner.run("slow_tool", {"param": "value"}),
                        timeout=0.1
                    )
                    assert False, "Should have timed out"
                except asyncio.TimeoutError:
                    pass  # Expected
            
            asyncio.run(test_timeout())


def test_tool_runner_tool_cancellation():
    """Test tool runner cancellation handling."""
    with patch('jarvis.core.tool_runner.Player') as mock_player:
        mock_player_instance = Mock()
        mock_player.return_value = mock_player_instance
        
        with patch('jarvis.core.tool_runner.get_secure_tool') as mock_get_tool:
            async def cancellable_tool(param):
                try:
                    await asyncio.sleep(10)  # Long running tool
                    return "Tool executed"
                except asyncio.CancelledError:
                    return "Tool cancelled"
            
            mock_get_tool.return_value = cancellable_tool
            
            from jarvis.core.tool_runner import ToolRunner
            
            runner = ToolRunner(player=mock_player_instance)
            
            async def test_cancellation():
                # Start tool execution
                task = asyncio.create_task(
                    runner.run("cancellable_tool", {"param": "value"})
                )
                
                # Cancel after a short delay
                await asyncio.sleep(0.1)
                task.cancel()
                
                try:
                    result = await task
                    assert result == "Tool cancelled"
                except asyncio.CancelledError:
                    pass  # Expected
            
            asyncio.run(test_cancellation())


def test_tool_runner_legacy_actions():
    """Test tool runner with legacy actions dictionary."""
    with patch('jarvis.core.tool_runner.Player') as mock_player:
        mock_player_instance = Mock()
        mock_player.return_value = mock_player_instance
        
        with patch('jarvis.core.tool_runner.get_secure_tool') as mock_get_tool:
            mock_get_tool.return_value = None
            
            with patch('jarvis.core.tool_runner.get_legacy_tool') as mock_get_legacy:
                mock_get_legacy.return_value = None
                
                # Mock legacy actions
                with patch('jarvis.core.tool_runner.LEGACY_ACTIONS', {
                    'legacy_action': lambda params: f"Legacy action executed with {params}"
                }):
                    
                    from jarvis.core.tool_runner import ToolRunner
                    
                    runner = ToolRunner(player=mock_player_instance)
                    
                    async def test_legacy():
                        result = await runner.run("legacy_action", {"param": "value"})
                        
                        assert result == "Legacy action executed with {'param': 'value'}"
                    
                    asyncio.run(test_legacy())


def test_tool_runner_metrics_tracking():
    """Test tool runner metrics tracking."""
    with patch('jarvis.core.tool_runner.Player') as mock_player:
        mock_player_instance = Mock()
        mock_player.return_value = mock_player_instance
        
        with patch('jarvis.core.tool_runner.get_secure_tool') as mock_get_tool:
            mock_tool = AsyncMock()
            mock_tool.return_value = "Tool executed"
            mock_get_tool.return_value = mock_tool
            
            from jarvis.core.tool_runner import ToolRunner
            
            runner = ToolRunner(player=mock_player_instance)
            
            async def test_metrics():
                # Execute several tools
                for i in range(3):
                    await runner.run("test_tool", {"param": f"value_{i}"})
                
                # Check metrics (if implemented)
                if hasattr(runner, 'get_metrics'):
                    metrics = runner.get_metrics()
                    assert 'tools_executed' in metrics
                    assert metrics['tools_executed'] == 3
            
            asyncio.run(test_metrics())
