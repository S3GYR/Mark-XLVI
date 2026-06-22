---
description: Refactor MARK XLVI into a modular, secure, production-ready architecture
---

# Refactor MARK XLVI

## Goal
Transform the monolithic MARK XLVI codebase into a modular assistant compatible with LiteLLM, PostgreSQL/pgvector, Hindsight, and Agent Zero patterns, while fixing P0 security vulnerabilities first.

## Phase 1 — Foundations & Security P0

1. Ensure `pyproject.toml` exists with modular extras.
2. Create `jarvis/` module structure.
3. Implement secure secret storage in `jarvis/security/secrets.py`.
4. Implement dynamic certificate generation in `jarvis/security/certs.py`.
5. Implement permission framework in `jarvis/security/permissions.py`.
6. Implement sandboxed code execution in `jarvis/security/sandbox.py`.
7. Replace `exec()` in `actions/desktop.py` with the new sandbox.
8. Replace `shell=True` in `actions/open_app.py` with the secure wrapper in `jarvis/tools/open_app.py`.

## Phase 2 — LLM Abstraction

1. Implement `jarvis/llm/client.py` using LiteLLM.
2. Implement `jarvis/llm/router.py` for multi-model fallback.
3. Add support for Gemini, OpenAI, Anthropic, DeepSeek, Mistral, Ollama.

## Phase 3 — Memory (PostgreSQL/pgvector)

1. Implement `jarvis/memory/store.py` abstract interface.
2. Implement `jarvis/memory/postgres_store.py`.
3. Keep JSON fallback in `jarvis/memory/json_store.py`.
4. Migrate legacy `memory/long_term.json` on first run.

## Phase 4 — Agent Patterns

1. Add planning loop with Hindsight-style memory.
2. Add tool-use agent loop in `jarvis/core/orchestrator.py`.
3. Add sub-agent support for complex tasks.

## Phase 5 — UI / Core Decoupling

1. Move `main.py` logic to `jarvis/core/orchestrator.py`.
2. Move `ui.py` components to `jarvis/ui/`.
3. Define `Player` protocol and decouple tools from PyQt6.

## Phase 6 — DevOps

1. Add Docker support.
2. Add GitHub Actions CI/CD.
3. Add tests for security, LLM, memory, tools.

## Verification

Run the new modular CLI:

```bash
uv sync --extra all
python -m jarvis.main
```

Run tests:

```bash
uv run pytest
```
