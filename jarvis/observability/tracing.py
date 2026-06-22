"""OpenTelemetry tracing and metrics setup."""

from __future__ import annotations

import os
from functools import wraps
from typing import Any, Callable, TypeVar

from jarvis.config.settings import get_settings

_F = TypeVar("_F", bound=Callable[..., Any])

_TRACING_CONFIGURED = False


def configure_tracing() -> None:
    """Configure OpenTelemetry if enabled."""
    global _TRACING_CONFIGURED
    if _TRACING_CONFIGURED:
        return

    settings = get_settings()
    if not os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT") and not settings.debug:
        # No OTLP endpoint configured, keep tracing disabled by default
        return

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource, SERVICE_NAME
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource(attributes={SERVICE_NAME: "jarvis"})
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter()
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        _TRACING_CONFIGURED = True
    except ImportError:
        pass


def get_tracer(name: str):
    """Return a tracer if OpenTelemetry is configured, else a no-op tracer."""
    try:
        from opentelemetry import trace
        return trace.get_tracer(name)
    except ImportError:
        return _NoOpTracer()


class _NoOpTracer:
    """No-op tracer used when OpenTelemetry is not installed."""

    def start_as_current_span(self, name: str, *args: Any, **kwargs: Any):
        class _NoOpSpan:
            def __enter__(self):
                return self

            def __exit__(self, *exc: Any):
                return False

            def set_attribute(self, *args: Any, **kwargs: Any):
                pass

            def record_exception(self, *args: Any, **kwargs: Any):
                pass

        return _NoOpSpan()


def instrument(name: str | None = None) -> Callable[[_F], _F]:
    """Decorator to trace a function."""

    def decorator(func: _F) -> _F:
        tracer = get_tracer(func.__module__)
        span_name = name or func.__name__

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with tracer.start_as_current_span(span_name):
                return func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


def instrument_async(name: str | None = None) -> Callable[[_F], _F]:
    """Decorator to trace an async function."""

    def decorator(func: _F) -> _F:
        tracer = get_tracer(func.__module__)
        span_name = name or func.__name__

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            with tracer.start_as_current_span(span_name):
                return await func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator
