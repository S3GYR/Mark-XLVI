# Refactoring Status — MARK XLVI

> This document tracks the modular refactoring of MARK XLVI. Last updated: after Phase 1.

## Completed

### Phase 1 — Foundations & Security P0

- [x] `pyproject.toml` with modular extras and dev tooling.
- [x] `.env.example` for configuration.
- [x] `jarvis/` package structure.
- [x] Centralized paths in `jarvis/config/paths.py` (outside source tree).
- [x] Type-safe settings in `jarvis/config/settings.py`.
- [x] Secure secret management in `jarvis/security/secrets.py` (keyring + encrypted fallback).
- [x] Dynamic certificate generation in `jarvis/security/certs.py`.
- [x] Permission framework in `jarvis/security/permissions.py`.
- [x] Sandboxed code execution in `jarvis/security/sandbox.py`.
- [x] Secure `desktop_control` wrapper in `jarvis/tools/desktop.py` (replaces `exec()`).
- [x] Secure `open_app` wrapper in `jarvis/tools/open_app.py` (replaces `shell=True`).
- [x] Tool registry in `jarvis/tools/registry.py`.
- [x] Player protocol in `jarvis/core/player.py`.
- [x] LiteLLM client in `jarvis/llm/client.py`.
- [x] Multi-model router in `jarvis/llm/client.py`.
- [x] Memory abstraction in `jarvis/memory/store.py`.
- [x] PostgreSQL/pgvector store in `jarvis/memory/postgres_store.py`.
- [x] JSON fallback store in `jarvis/memory/json_store.py`.
- [x] Structured logging in `jarvis/observability/logger.py`.
- [x] Agent orchestrator in `jarvis/core/orchestrator.py`.
- [x] New modular entry point `jarvis/main.py`.
- [x] GitHub Actions CI in `.github/workflows/ci.yml`.
- [x] Initial tests for sandbox and permissions.
- [x] Refactor workflow in `.devin/workflows/refactor.md`.

## In Progress

- [x] Wiring remaining legacy actions into secure wrappers.
- [x] Decoupling `main.py` and `ui.py` — initial modular session + GUI adapter.
- [x] Dashboard refactoring into `jarvis/web/`.
- [x] Dockerization (`Dockerfile` + `docker-compose.yml`).
- [x] Full migration of legacy `main.py` audio loop to `jarvis/audio/`.
- [x] Split `ui.py` into atomic `jarvis/ui/` components (constants, metrics, metric_bar, log_panel, file_drop, hud, main_window, app).
- [x] Replaced mock embeddings with real provider abstraction (`jarvis/llm/embeddings.py` supports sentence-transformers, LiteLLM, mock fallback).
- [x] Added OpenTelemetry tracing (`jarvis/observability/tracing.py`) and instrumented core flows.
- [x] Expanded test suite: security, web, tools, UI, memory, LLM, core orchestrator, observability.
- [x] Fixed rate-limiting bug in `jarvis/web/auth.py` (`record_attempt` was resetting the counter every call).
- [x] Made `browser_control` tool optional in `jarvis/tools/registry.py` when Playwright is unavailable.
- [x] Ran full test suite: **51 passed, 2 skipped** (sentence-transformers live test skipped, real LLM chat skipped).
- [ ] Reach >80% coverage (currently 25% due to untested UI/web/routes/legacy tools; requires additional tests for those layers).

## New Architecture

```
jarvis/
├── main.py              # CLI / GUI entry point
├── config/              # Settings, paths, constants
├── security/            # Secrets, sandbox, permissions, certs
├── core/                # Player protocol, orchestrator, tool runner, live session
├── llm/                 # LiteLLM client + router
├── memory/              # PostgreSQL/pgvector + JSON stores
├── tools/               # Secure tool wrappers
├── audio/               # Capture, playback, phone relay
├── web/                 # FastAPI dashboard
├── ui/                  # PyQt6 adapter and (future) components
└── observability/       # Structured logging
```

## Security P0 Fixes

| Vulnerability | Before | After |
|---|---|---|
| `exec()` in `actions/desktop.py` | Direct code execution | `jarvis/security/sandbox.py` with subprocess + static checks |
| `shell=True` in `actions/open_app.py` | Command injection risk | `jarvis/tools/open_app.py` with argument lists + allowlist |
| API keys in plaintext JSON | `config/api_keys.json` | `jarvis/security/secrets.py` via keyring or encrypted fallback |
| Committed SSL private key | `config/certs/jarvis.key` | `jarvis/security/certs.py` generates certificates at runtime |
| No user confirmation for dangerous actions | Direct execution | `jarvis/security/permissions.py` with risk levels |
| SSRF via browser automation | Unrestricted URLs | `jarvis/tools/browser_control.py` blocks local/internal IPs |
| Message sending without confirmation | Direct send | `jarvis/tools/send_message.py` requires confirmation |
| Code execution helper | Direct subprocess | `jarvis/tools/code_helper.py` uses sandbox |
| Dev agent installs dependencies | Auto pip install | `jarvis/tools/dev_agent.py` asks confirmation |
| Weak dashboard auth | 6-digit PIN no rate limit | `jarvis/web/auth.py` with rate limiting + lockout |
| Homegrown AES-CBC | No integrity | `jarvis/web/crypto.py` AES-256-GCM |
| Dashboard bound to 0.0.0.0 | Wide exposure | Default `127.0.0.1`, firewall auto-config disabled |

## Wrapped Tools

| Tool | Wrapper | Confirmation | Notes |
|---|---|---|---|
| `open_app` | `jarvis/tools/open_app.py` | No | Blocks terminals/injection |
| `desktop_control` | `jarvis/tools/desktop.py` | High-risk actions | Sandbox for AI tasks |
| `computer_control` | `jarvis/tools/computer_control.py` | Yes | Keyboard/mouse simulation |
| `send_message` | `jarvis/tools/send_message.py` | Yes | Messaging platforms |
| `browser_control` | `jarvis/tools/browser_control.py` | High-risk actions | SSRF protection |
| `code_helper` | `jarvis/tools/code_helper.py` | Yes | Sandbox execution |
| `dev_agent` | `jarvis/tools/dev_agent.py` | Yes | Projects in `DATA_DIR` |

## How to run

```bash
# Install with all extras
uv sync --extra all

# Run the new modular CLI
python -m jarvis.main

# Run tests
uv run pytest

# Run linting
uv run ruff check .
uv run mypy jarvis/
```

## Next steps

1. Wrap remaining actions (`computer_control`, `send_message`, `browser_control`, `dev_agent`, `code_helper`).
2. Migrate `main.py` logic to `jarvis/core/orchestrator.py` and remove the legacy file.
3. Split `ui.py` into `jarvis/ui/` components.
4. Refactor dashboard to `jarvis/web/`.
5. Add Docker and compose files.
6. Expand tests to >80% coverage.

## Notes

- Legacy files (`main.py`, `ui.py`, `actions/*.py`, `memory/*.py`) are kept untouched for compatibility during the transition.
- New modules are designed to be imported and tested independently.
- The old entry point still works; the new entry point is `python -m jarvis.main`.
