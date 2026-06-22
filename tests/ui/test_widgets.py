"""Widget tests for PyQt6 UI components."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock
import asyncio
from typing import Any


def test_ui_widget_imports():
    """Test that UI widget modules import correctly."""
    try:
        from jarvis.ui.constants import UI_COLORS, UI_FONTS, UI_DIMENSIONS
        from jarvis.ui.metrics import UIMetrics
        from jarvis.ui.metric_bar import MetricBar
        from jarvis.ui.log_panel import LogPanel
        from jarvis.ui.file_drop import FileDropWidget
        from jarvis.ui.hud import HUD
        from jarvis.ui.main_window import JarvisMainWindow
        from jarvis.ui.app import JarvisApp
        
        assert all(module is not None for module in [
            UI_COLORS, UI_FONTS, UI_DIMENSIONS, UIMetrics, 
            MetricBar, LogPanel, FileDropWidget, HUD, 
            JarvisMainWindow, JarvisApp
        ])
    except ImportError as e:
        pytest.fail(f"Failed to import UI modules: {e}")


def test_ui_constants():
    """Test UI constants are properly defined."""
    from jarvis.ui.constants import UI_COLORS, UI_FONTS, UI_DIMENSIONS
    
    # Test colors
    assert isinstance(UI_COLORS, dict)
    assert 'primary' in UI_COLORS
    assert 'secondary' in UI_COLORS
    assert 'background' in UI_COLORS
    assert 'text' in UI_COLORS
    
    # Test fonts
    assert isinstance(UI_FONTS, dict)
    assert 'primary' in UI_FONTS
    assert 'secondary' in UI_FONTS
    assert 'monospace' in UI_FONTS
    
    # Test dimensions
    assert isinstance(UI_DIMENSIONS, dict)
    assert 'window_width' in UI_DIMENSIONS
    assert 'window_height' in UI_DIMENSIONS
    assert 'padding' in UI_DIMENSIONS


def test_ui_metrics():
    """Test UI metrics functionality."""
    with patch('jarvis.ui.metrics.QTimer') as mock_timer:
        with patch('jarvis.ui.metrics.time') as mock_time:
            mock_time.time.return_value = 1234567890.0
            
            from jarvis.ui.metrics import UIMetrics
            
            # Test initialization
            metrics = UIMetrics()
            assert metrics is not None
            
            # Test metrics tracking
            metrics.add_metric("cpu_usage", 75.5)
            metrics.add_metric("memory_usage", 60.2)
            
            # Test metrics retrieval
            cpu_metric = metrics.get_metric("cpu_usage")
            assert cpu_metric is not None
            assert cpu_metric.value == 75.5
            
            # Test metrics history
            history = metrics.get_metric_history("cpu_usage", 10)
            assert len(history) > 0


def test_metric_bar():
    """Test metric bar widget."""
    with patch('jarvis.ui.metric_bar.QWidget') as mock_widget:
        with patch('jarvis.ui.metric_bar.QProgressBar') as mock_progress:
            with patch('jarvis.ui.metric_bar.QLabel') as mock_label:
                
                from jarvis.ui.metric_bar import MetricBar
                
                # Test initialization
                metric_bar = MetricBar("Test Metric", "cpu")
                assert metric_bar is not None
                assert metric_bar.metric_name == "Test Metric"
                assert metric_bar.metric_type == "cpu"
                
                # Test value update
                metric_bar.update_value(85.0)
                # Should update the progress bar
                
                # Test color updates
                metric_bar.update_color("red")
                metric_bar.update_color("green")


def test_log_panel():
    """Test log panel widget."""
    with patch('jarvis.ui.log_panel.QWidget') as mock_widget:
        with patch('jarvis.ui.log_panel.QTextEdit') as mock_text:
            with patch('jarvis.ui.log_panel.QVBoxLayout') as mock_layout:
                
                from jarvis.ui.log_panel import LogPanel
                
                # Test initialization
                log_panel = LogPanel()
                assert log_panel is not None
                
                # Test log addition
                log_panel.add_log("INFO", "Test message")
                log_panel.add_log("ERROR", "Error message")
                log_panel.add_log("DEBUG", "Debug message")
                
                # Test log clearing
                log_panel.clear_logs()
                
                # Test log filtering
                log_panel.filter_logs("INFO")
                log_panel.filter_logs("ERROR")


def test_file_drop_widget():
    """Test file drop widget."""
    with patch('jarvis.ui.file_drop.QWidget') as mock_widget:
        with patch('jarvis.ui.file_drop.QLabel') as mock_label:
            with patch('jarvis.ui.file_drop.QVBoxLayout') as mock_layout:
                
                from jarvis.ui.file_drop import FileDropWidget
                
                # Test initialization
                file_drop = FileDropWidget()
                assert file_drop is not None
                
                # Test file drop handling
                mock_mime_data = Mock()
                mock_mime_data.hasUrls.return_value = True
                mock_mime_data.urls.return_value = [
                    Mock(path=lambda: "/path/to/file1.txt"),
                    Mock(path=lambda: "/path/to/file2.txt")
                ]
                
                # Simulate drop event
                file_drop.handle_drop(mock_mime_data)
                
                # Test drag enter event
                file_drop.handle_drag_enter(mock_mime_data)
                
                # Test drag leave event
                file_drop.handle_drag_leave()


def test_hud():
    """Test HUD widget."""
    with patch('jarvis.ui.hud.QWidget') as mock_widget:
        with patch('jarvis.ui.hud.QLabel') as mock_label:
            with patch('jarvis.ui.hud.QGridLayout') as mock_layout:
                
                from jarvis.ui.hud import HUD
                
                # Test initialization
                hud = HUD()
                assert hud is not None
                
                # Test status updates
                hud.update_status("Ready")
                hud.update_status("Processing")
                hud.update_status("Complete")
                
                # Test progress updates
                hud.update_progress(25)
                hud.update_progress(50)
                hud.update_progress(100)
                
                # Test message display
                hud.show_message("Test message")
                hud.show_error("Error message")
                hud.show_warning("Warning message")


def test_main_window():
    """Test main window widget."""
    with patch('jarvis.ui.main_window.QMainWindow') as mock_main:
        with patch('jarvis.ui.main_window.QMenuBar') as mock_menubar:
            with patch('jarvis.ui.main_window.QStatusBar') as mock_status:
                with patch('jarvis.ui.main_window.QCentralWidget') as mock_central:
                    
                    from jarvis.ui.main_window import JarvisMainWindow
                    
                    # Test initialization
                    main_window = JarvisMainWindow()
                    assert main_window is not None
                    
                    # Test window setup
                    main_window.setup_ui()
                    main_window.setup_menu()
                    main_window.setup_status_bar()
                    
                    # Test panel management
                    main_window.add_log_panel()
                    main_window.add_metrics_panel()
                    main_window.add_hud_panel()
                    
                    # Test window state
                    main_window.show()
                    main_window.hide()
                    main_window.close()


def test_jarvis_app():
    """Test Jarvis application."""
    with patch('jarvis.ui.app.QApplication') as mock_qapp:
        with patch('jarvis.ui.app.JarvisMainWindow') as mock_main:
            
            from jarvis.ui.app import JarvisApp
            
            # Test initialization
            app = JarvisApp([])
            assert app is not None
            
            # Test setup
            app.setup_ui()
            app.setup_connections()
            
            # Test execution
            app.run()
            
            # Test cleanup
            app.cleanup()


def test_ui_integration():
    """Test UI component integration."""
    with patch('jarvis.ui.metrics.QTimer'):
        with patch('jarvis.ui.metrics.time'):
            with patch('jarvis.ui.metric_bar.QWidget'):
                with patch('jarvis.ui.log_panel.QWidget'):
                    with patch('jarvis.ui.hud.QWidget'):
                        with patch('jarvis.ui.main_window.QMainWindow'):
                            
                            from jarvis.ui.metrics import UIMetrics
                            from jarvis.ui.metric_bar import MetricBar
                            from jarvis.ui.log_panel import LogPanel
                            from jarvis.ui.hud import HUD
                            from jarvis.ui.main_window import JarvisMainWindow
                            
                            # Test component creation
                            metrics = UIMetrics()
                            metric_bar = MetricBar("CPU", "cpu")
                            log_panel = LogPanel()
                            hud = HUD()
                            main_window = JarvisMainWindow()
                            
                            # Test component interaction
                            metrics.add_metric("cpu", 75.0)
                            metric_bar.update_value(75.0)
                            log_panel.add_log("INFO", "CPU usage updated")
                            hud.update_progress(75)


def test_ui_error_handling():
    """Test UI error handling."""
    with patch('jarvis.ui.metrics.QTimer'):
        with patch('jarvis.ui.metrics.time'):
            
            from jarvis.ui.metrics import UIMetrics
            
            metrics = UIMetrics()
            
            # Test invalid metric values
            try:
                metrics.add_metric("invalid", "not_a_number")
                # Should handle gracefully
            except (ValueError, TypeError):
                pass  # Expected
            
            # Test missing metrics
            missing_metric = metrics.get_metric("nonexistent")
            assert missing_metric is None
            
            # Test empty history
            empty_history = metrics.get_metric_history("nonexistent", 10)
            assert empty_history == []


def test_ui_theme_styling():
    """Test UI theme styling."""
    from jarvis.ui.constants import UI_COLORS, UI_FONTS, UI_DIMENSIONS
    
    # Test color values
    assert UI_COLORS['primary'] != ""
    assert UI_COLORS['secondary'] != ""
    assert UI_COLORS['background'] != ""
    assert UI_COLORS['text'] != ""
    
    # Test font values
    assert UI_FONTS['primary'] != ""
    assert UI_FONTS['secondary'] != ""
    assert UI_FONTS['monospace'] != ""
    
    # Test dimension values
    assert UI_DIMENSIONS['window_width'] > 0
    assert UI_DIMENSIONS['window_height'] > 0
    assert UI_DIMENSIONS['padding'] >= 0


def test_ui_responsive_layout():
    """Test UI responsive layout."""
    with patch('jarvis.ui.main_window.QMainWindow'):
        with patch('jarvis.ui.main_window.QResizeEvent'):
            
            from jarvis.ui.main_window import JarvisMainWindow
            
            main_window = JarvisMainWindow()
            
            # Test window resize handling
            mock_event = Mock()
            mock_event.size.return_value = Mock(width=800, height=600)
            
            main_window.resizeEvent(mock_event)
            
            # Test layout adaptation
            main_window.adapt_layout(800, 600)
            main_window.adapt_layout(1200, 800)
            main_window.adapt_layout(400, 300)


def test_ui_accessibility():
    """Test UI accessibility features."""
    with patch('jarvis.ui.metric_bar.QWidget'):
        with patch('jarvis.ui.metric_bar.QProgressBar'):
            
            from jarvis.ui.metric_bar import MetricBar
            
            metric_bar = MetricBar("CPU Usage", "cpu")
            
            # Test accessibility attributes
            metric_bar.set_accessibility_name("CPU Usage Metric")
            metric_bar.set_accessibility_description("Shows current CPU usage percentage")
            
            # Test keyboard navigation
            metric_bar.set_focus_policy("tab")
            metric_bar.set_shortcut("Ctrl+C")


def test_ui_performance():
    """Test UI performance optimization."""
    with patch('jarvis.ui.metrics.QTimer'):
        with patch('jarvis.ui.metrics.time'):
            
            from jarvis.ui.metrics import UIMetrics
            
            metrics = UIMetrics()
            
            # Test performance with many metrics
            import time
            start_time = time.time()
            
            for i in range(1000):
                metrics.add_metric(f"metric_{i}", i % 100)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Should handle 1000 metrics efficiently
            assert processing_time < 1.0  # Should complete in under 1 second
            
            # Test cleanup performance
            start_time = time.time()
            metrics.cleanup_old_metrics(100)
            end_time = time.time()
            
            cleanup_time = end_time - start_time
            assert cleanup_time < 0.5  # Should cleanup in under 0.5 seconds

    QApplication.instance() or QApplication([])
    w = JarvisMainWindow()
    qtbot.addWidget(w)
    return w


def test_constants():
    """UI constants are populated."""
    assert C.PRI == "#00d4ff"
    assert DEFAULT_W > 0
    assert DEFAULT_H > 0


def test_metric_bar(qtbot):
    """MetricBar accepts value updates."""
    bar = MetricBar("CPU", C.PRI)
    qtbot.addWidget(bar)
    bar.set_value(75.0, "75%")
    assert bar._value == 75.0
    assert bar._text == "75%"


def test_log_widget(qtbot):
    """LogWidget appends text."""
    log = LogWidget()
    qtbot.addWidget(log)
    log.append_log("test message")
    # Wait for typewriter animation to complete
    qtbot.waitUntil(lambda: "test message" in log.toPlainText(), timeout=1000)
    assert "test message" in log.toPlainText()


def test_file_drop_zone(qtbot):
    """FileDropZone has expected label."""
    drop = FileDropZone()
    qtbot.addWidget(drop)
    assert drop._label is not None


def test_hud_canvas(qtbot):
    """HudCanvas can update state."""
    hud = HudCanvas()
    qtbot.addWidget(hud)
    hud.state = "LISTENING"
    assert hud.state == "LISTENING"


def test_main_window_title(window: JarvisMainWindow):
    """Main window has the expected title."""
    assert "JARVIS" in window.windowTitle()


def test_main_window_set_state(window: JarvisMainWindow):
    """Main window state updates HUD and status."""
    window.set_state("THINKING")
    assert window._hud.state == "THINKING"
    assert "THINKING" in window._status.text()


def test_main_window_log(window: JarvisMainWindow, qtbot):
    """Main window log widget receives text."""
    window.write_log("hello")
    # Wait for typewriter animation to complete
    qtbot.waitUntil(lambda: "hello" in window._log.toPlainText(), timeout=1000)
    assert "hello" in window._log.toPlainText()
