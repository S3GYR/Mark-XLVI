"""Tests for system metrics."""

from __future__ import annotations

from jarvis.ui.metrics import SystemMetrics


def test_snapshot_contains_expected_keys():
    """Snapshot has the expected metric keys."""
    metrics = SystemMetrics()
    snap = metrics.snapshot()
    for key in ("cpu", "memory", "network", "gpu", "temperature"):
        assert key in snap


def test_gpu_temperature_defaults():
    """GPU and temperature are numbers or -1."""
    metrics = SystemMetrics()
    snap = metrics.snapshot()
    assert isinstance(snap["gpu"], (int, float))
    assert isinstance(snap["temperature"], (int, float))
    metrics.stop()
