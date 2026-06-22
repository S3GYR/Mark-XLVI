# Architecture — MARK XLVI (Modular Refactor)

> High-level architecture of the refactored JARVIS assistant.

## 1. Overview

The refactored MARK XLVI is split into a **headless core** and optional **UI/dashboard** layers. The core is designed to run independently, enabling CLI usage, containerization, and future remote deployments.

## 2. Module Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         Interfaces                           │
│  CLI (jarvis/main.py)  │  GUI (jarvis/ui/app.py)  │  Dashboard │
└──────────┬─────────────────────────┬─────────────────────────┘
           │                         │
           ▼                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     Core (jarvis/core)                       │
│  Orchestrator │ Live Session │ Tool Runner │ Player Protocol │
└──────────┬──────────────────────────────────────────────────┘
           │
    ┌──────┴──────┬─────────────┬─────────────┐
    ▼             ▼             ▼             ▼
jarvis/llm    jarvis/memory  jarvis/tools  jarvis/audio
(LiteLLM)   (pgvector)   (wrappers)   (sounddevice)
    │             │             │             │
    ▼             ▼             ▼             ▼
Gemini/      PostgreSQL/    Legacy        PyAudio
OpenAI/      JSON           actions       pipelines
Anthropic/                  (actions/)
Ollama/
DeepSeek/
Mistral
```

## 3. Core Modules

### 3.1 `jarvis/config`

- `paths.py` — centralized path management outside the source tree.
- `settings.py` — Pydantic settings loaded from `.env` and environment variables.

### 3.2 `jarvis/security`

- `secrets.py` — API key storage via keyring or encrypted fallback.
- `certs.py` — dynamic self-signed certificate generation.
- `permissions.py` — risk-level based user confirmation.
- `sandbox.py` — subprocess-based sandbox for LLM-generated code.

### 3.3 `jarvis/core`

- `player.py` — protocol decoupling tools from the UI.
- `orchestrator.py` — Hindsight/Agent Zero inspired planning and execution loop.
- `tool_runner.py` — bridge between secure wrappers and legacy actions.
- `live_session.py` — Gemini Live audio session management.

### 3.4 `jarvis/llm`

- `client.py` — LiteLLM-based unified client supporting multiple providers.
- `router.py` — multi-model fallback and routing.

### 3.5 `jarvis/memory`

- `store.py` — abstract memory interface.
- `postgres_store.py` — PostgreSQL + pgvector implementation.
- `json_store.py` — JSON fallback for local development.

### 3.6 `jarvis/tools`

- `registry.py` — tool declarations and dispatch.
- `open_app.py`, `desktop.py`, `computer_control.py`, `send_message.py`, `browser_control.py`, `code_helper.py`, `dev_agent.py` — secure wrappers.

### 3.7 `jarvis/audio`

- `capture.py` — microphone input.
- `playback.py` — speaker output.
- `phone_relay.py` — phone audio streaming bridge.

### 3.8 `jarvis/web`

- `server.py` — FastAPI application factory.
- `auth.py` — PIN/tokens with rate limiting.
- `crypto.py` — AES-256-GCM encryption.
- `routes/` — commands, uploads, WebSocket endpoints.

### 3.9 `jarvis/ui`

- `app.py` — PyQt6 GUI entry point and adapter for legacy UI.
- Future components: `main_window.py`, `hud_canvas.py`, `metrics.py`, etc.

### 3.10 `jarvis/observability`

- `logger.py` — structured logging with `structlog`.

## 4. Data Flow

### 4.1 Voice Interaction

1. `AudioCapture` reads microphone frames.
2. Frames are queued to `GeminiLiveSession._send_realtime()`.
3. `GeminiLiveSession` streams to Gemini Live API.
4. Gemini returns audio and/or tool calls.
5. `AudioPlayback` plays response audio.
6. Tool calls are routed through `ToolRunner`.

### 4.2 Text Command

1. `JarvisAssistant` receives text input.
2. `AgentOrchestrator` loads memory and calls LLM via `LLMClient`.
3. LLM returns a plan or direct tool calls.
4. `ToolRunner` executes secure wrappers or legacy actions.
5. Results are stored in memory and returned to the user.

### 4.3 Dashboard

1. `DashboardServer` exposes FastAPI routes.
2. User authenticates via PIN/QR code.
3. Commands are encrypted with AES-256-GCM.
4. Commands are queued to the orchestrator.
5. File uploads are stored in `DATA_DIR/uploads`.

## 5. Security Model

- **Secrets**: stored in OS keyring or encrypted file, never in plaintext JSON.
- **Certificates**: generated at runtime, never committed.
- **Code execution**: sandboxed with subprocess, static analysis, timeout.
- **System control**: confirmation required for high-risk actions.
- **Browser**: SSRF protection blocks local/internal IPs.
- **Dashboard**: rate-limited PIN, bearer tokens, AES-GCM encryption.
- **Network**: default `127.0.0.1`, firewall auto-config disabled by default.

## 6. Extensibility

- New tools: implement the function signature and register in `jarvis/tools/registry.py`.
- New LLM providers: add model prefix to `LLMClient`.
- New memory backends: implement `MemoryStore`.
- New UI: implement the `Player` protocol.

## 7. Deployment Targets

- **Local CLI**: `python -m jarvis.main`
- **Local GUI**: `python -m jarvis.main --gui`
- **Docker**: `docker compose up`
- **Headless server**: `docker compose up` without `--gui`

## 8. Future Work

- Split `ui.py` into atomic widgets.
- Add WebRTC audio for browser-based clients.
- Add OpenTelemetry tracing.
- Expand test coverage to >80%.
- Add vector-based semantic search with real embeddings.
- Integrate LiteLLM proxy for observability.
