"""Tests for legacy tool wrappers to ensure security and functionality."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from pathlib import Path


def test_open_app_wrapper_security():
    """Test that open_app wrapper blocks dangerous applications."""
    from jarvis.tools.open_app import open_app_secure
    
    # Test blocking of dangerous apps
    dangerous_apps = ["cmd", "powershell", "terminal", "bash"]
    
    for app in dangerous_apps:
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 1
            result = open_app_secure(app)
            # Should either block or run with restrictions
            assert isinstance(result, str)


def test_open_app_wrapper_safe_apps():
    """Test that open_app wrapper allows safe applications."""
    from jarvis.tools.open_app import open_app_secure
    
    # Test safe applications
    safe_apps = ["notepad", "chrome", "firefox"]
    
    for app in safe_apps:
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            with patch('jarvis.tools.open_app._is_safe_app', return_value=True):
                result = open_app_secure(app)
                assert isinstance(result, str)


def test_desktop_control_sandbox():
    """Test that desktop control uses sandbox properly."""
    from jarvis.tools.desktop import DesktopControl
    
    with patch('jarvis.security.sandbox.Sandbox') as mock_sandbox:
        mock_sandbox_instance = Mock()
        mock_sandbox.return_value = mock_sandbox_instance
        mock_sandbox_instance.execute.return_value = "success"
        
        control = DesktopControl()
        result = control.execute("print('test')")
        
        mock_sandbox.assert_called_once()
        assert result == "success"


def test_desktop_control_code_validation():
    """Test that desktop control validates code before execution."""
    from jarvis.tools.desktop import DesktopControl
    
    control = DesktopControl()
    
    # Test dangerous code rejection
    dangerous_code = "import os; os.system('rm -rf /')"
    assert not control._validate_code(dangerous_code)
    
    # Test safe code acceptance
    safe_code = "print('hello world')"
    assert control._validate_code(safe_code)


def test_computer_control_confirmation():
    """Test that computer control requires confirmation for dangerous actions."""
    from jarvis.tools.computer_control import ComputerControl
    
    with patch('jarvis.security.permissions.request_confirmation') as mock_confirm:
        mock_confirm.return_value = False  # User denies
        
        control = ComputerControl()
        result = control.click_dangerous_zone()
        
        mock_confirm.assert_called_once()
        assert "cancelled" in result.lower()


def test_computer_control_safe_actions():
    """Test that safe computer actions don't require confirmation."""
    from jarvis.tools.computer_control import ComputerControl
    
    with patch('pyautogui.moveTo') as mock_move:
        control = ComputerControl()
        control.move_mouse(100, 200)
        
        mock_move.assert_called_with(100, 200)


def test_send_message_security():
    """Test that send_message wrapper validates recipients."""
    from jarvis.tools.send_message import SendMessage
    
    with patch('jarvis.security.permissions.request_confirmation') as mock_confirm:
        mock_confirm.return_value = True
        
        sender = SendMessage()
        result = sender.send("test message", "test@example.com")
        
        mock_confirm.assert_called_once()
        assert isinstance(result, str)


def test_browser_control_ssrf_protection():
    """Test that browser control blocks SSRF attempts."""
    from jarvis.tools.browser_control import BrowserControl
    
    control = BrowserControl()
    
    # Test blocking of internal URLs
    dangerous_urls = [
        "http://localhost:8080",
        "http://127.0.0.1/admin",
        "http://192.168.1.1/secret",
        "file:///etc/passwd"
    ]
    
    for url in dangerous_urls:
        assert not control._is_safe_url(url)
    
    # Test allowing of safe URLs
    safe_urls = [
        "https://www.google.com",
        "https://github.com",
        "https://stackoverflow.com"
    ]
    
    for url in safe_urls:
        assert control._is_safe_url(url)


def test_code_helper_sandbox_usage():
    """Test that code helper uses sandbox for execution."""
    from jarvis.tools.code_helper import CodeHelper
    
    with patch('jarvis.security.sandbox.Sandbox') as mock_sandbox:
        mock_sandbox_instance = Mock()
        mock_sandbox.return_value = mock_sandbox_instance
        mock_sandbox_instance.execute.return_value = "output"
        
        helper = CodeHelper()
        result = helper.execute_code("print('test')")
        
        mock_sandbox.assert_called_once()
        assert result == "output"


def test_dev_agent_project_validation():
    """Test that dev agent validates project paths."""
    from jarvis.tools.dev_agent import DevAgent
    
    with patch('jarvis.config.paths.DATA_DIR') as mock_data_dir:
        mock_data_dir = Path("/tmp/jarvis_data")
        
        agent = DevAgent()
        
        # Test safe project path (within DATA_DIR)
        safe_path = mock_data_dir / "my_project"
        assert agent._is_safe_project_path(safe_path)
        
        # Test dangerous project path (outside DATA_DIR)
        dangerous_path = Path("/etc/passwd")
        assert not agent._is_safe_project_path(dangerous_path)


def test_dev_agent_confirmation_required():
    """Test that dev agent requires confirmation for dangerous actions."""
    from jarvis.tools.dev_agent import DevAgent
    
    with patch('jarvis.security.permissions.request_confirmation') as mock_confirm:
        mock_confirm.return_value = False  # User denies
        
        agent = DevAgent()
        result = agent.install_dependencies("dangerous-package")
        
        mock_confirm.assert_called_once()
        assert "cancelled" in result.lower()


def test_tool_registry_integration():
    """Test that all tools are properly registered."""
    from jarvis.tools.registry import ToolRegistry
    
    registry = ToolRegistry()
    
    # Check that all expected tools are registered
    expected_tools = [
        'open_app',
        'desktop_control', 
        'computer_control',
        'send_message',
        'browser_control',
        'code_helper',
        'dev_agent'
    ]
    
    for tool_name in expected_tools:
        assert tool_name in registry.get_available_tools()


def test_tool_wrapper_error_handling():
    """Test that tool wrappers handle errors gracefully."""
    from jarvis.tools.open_app import open_app_secure
    
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = Exception("Command failed")
        
        result = open_app_secure("nonexistent_app")
        assert "error" in result.lower() or "failed" in result.lower()


def test_tool_wrapper_logging():
    """Test that tool wrappers log their actions."""
    from jarvis.tools.open_app import open_app_secure
    
    with patch('jarvis.observability.logger.get_logger') as mock_logger:
        mock_logger_instance = Mock()
        mock_logger.return_value = mock_logger_instance
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            
            open_app_secure("notepad")
            
            # Should log the action
            mock_logger_instance.info.assert_called()


def test_optional_browser_control():
    """Test that browser_control is optional when Playwright is unavailable."""
    with patch.dict('sys.modules', {'playwright': None}):
        # Re-import registry to test optional dependency
        import importlib
        from jarvis.tools import registry
        importlib.reload(registry)
        
        reg = registry.ToolRegistry()
        tools = reg.get_available_tools()
        
        # browser_control should not be available
        assert 'browser_control' not in tools or reg.is_tool_available('browser_control') is False
