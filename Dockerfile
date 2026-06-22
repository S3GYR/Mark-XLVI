# syntax=docker/dockerfile:1
FROM python:3.12-slim

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libportaudio2 \
    libasound2-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /uvx /bin/

# Copy dependency definitions
COPY pyproject.toml readme.md ./

# Install project dependencies (core + dashboard + memory)
RUN uv sync --extra dashboard --extra memory --extra vision

# Copy application code
COPY jarvis/ ./jarvis/
COPY actions/ ./actions/
COPY core/ ./core/
COPY memory/ ./memory/
COPY dashboard/ ./dashboard/
COPY ui.py ./ui.py
COPY main.py ./main.py

# Create non-root user
RUN useradd -m -u 1000 jarvis && chown -R jarvis:jarvis /app
USER jarvis

# Expose dashboard port
EXPOSE 8000

# Default: run the modular CLI
CMD ["uv", "run", "python", "-m", "jarvis.main"]
