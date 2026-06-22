"""Tests for tracing helpers."""

from __future__ import annotations

import asyncio

from jarvis.observability.tracing import instrument, instrument_async


@instrument("test.sync")
def sync_func(x: int) -> int:
    return x * 2


@instrument_async("test.async")
async def async_func(x: int) -> int:
    return x + 1


def test_sync_instrumentation():
    """Decorator does not change sync function behavior."""
    assert sync_func(5) == 10


def test_async_instrumentation():
    """Decorator does not change async function behavior."""
    assert asyncio.run(async_func(4)) == 5


def test_no_op_tracer():
    """No-op tracer works without OpenTelemetry installed."""
    from jarvis.observability.tracing import get_tracer

    tracer = get_tracer("test")
    with tracer.start_as_current_span("span"):
        assert True
