# Roadmap de refactoring — MARK XLVI

> Ce document propose un découpage architectural concret du projet pour le rendre maintenable, testable et prêt pour une utilisation professionnelle. Aucun fichier source n'est modifié : ce document est un plan de travail.

## 1. Objectifs du refactoring

1. **Réduire la taille des fichiers** : aucun fichier ne doit dépasser 300-400 lignes.
2. **Séparer les responsabilités** : UI, core, audio, web, outils, mémoire, config doivent être isolés.
3. **Supprimer les duplications** : `get_base_dir`, lecture de clé API, etc.
4. **Rendre le code testable** : injection de dépendances, protocoles, mocks.
5. **Préparer la conteneurisation** : rendre le core exécutable sans UI graphique.
6. **Sécuriser** : supprimer les `exec()`, `shell=True`, clés commitées.

## 2. Découpage recommandé de `main.py`

`main.py` fait actuellement 969 lignes. Il contient :

- Constantes audio (`main.py:46-50`)
- Déclarations des outils (`TOOL_DECLARATIONS`, `main.py:74-466`)
- Chargement de la clé API et du prompt (`main.py:52-65`)
- Classe `JarvisLive` avec orchestration Gemini (`main.py:471-953`)
- Point d'entrée (`main()`)

### 2.1 Modules à extraire de `main.py`

| Module cible | Contenu extrait de `main.py` | Lignes concernées |
|---|---|---|
| `jarvis/config/audio.py` | Constantes audio (`LIVE_MODEL`, `CHANNELS`, `SEND_SAMPLE_RATE`, `RECEIVE_SAMPLE_RATE`, `CHUNK_SIZE`) | `main.py:46-50` |
| `jarvis/config/paths.py` | `get_base_dir()`, `BASE_DIR`, `API_CONFIG_PATH`, `PROMPT_PATH` | `main.py:37-40`, `43-45` |
| `jarvis/config/keys.py` | `_get_api_key()`, `_load_system_prompt()` | `main.py:52-65` |
| `jarvis/tools/registry.py` | `TOOL_DECLARATIONS` + helpers de déclaration | `main.py:74-466` |
| `jarvis/core/orchestrator.py` | Classe `JarvisLive` : connexion, session, reconnexion | `main.py:471-560`, `890-953` |
| `jarvis/core/tool_dispatcher.py` | `_execute_tool()` + mapping nom → fonction | `main.py:571-697` |
| `jarvis/audio/capture.py` | `_listen_audio()` | `main.py:704-731` |
| `jarvis/audio/playback.py` | `_receive_audio()` et `_play_audio()` | `main.py:733-834` |
| `jarvis/audio/phone_relay.py` | `_relay_phone_audio()` | `main.py:836-853` |
| `jarvis/dashboard/connector.py` | Intégration dashboard (`_process_dashboard_commands`, `_on_phone_connected`) | `main.py:855-887` |
| `jarvis/main.py` | Point d'entrée allégé | `main.py:954-969` |

### 2.2 Architecture cible du core

```
jarvis/
├── main.py                    # point d'entrée (30 lignes)
├── config/
│   ├── __init__.py
│   ├── audio.py              # constantes audio
│   ├── paths.py              # get_base_dir, chemins
│   └── keys.py               # clé API, prompt système
├── core/
│   ├── orchestrator.py       # JarvisLive, gestion session
│   ├── tool_dispatcher.py    # mapping outils
│   └── state.py              # état global (muted, speaking, etc.)
├── audio/
│   ├── capture.py
│   ├── playback.py
│   └── phone_relay.py
├── llm/
│   ├── client.py             # abstraction LLM
│   ├── gemini_client.py      # implémentation Gemini Live
│   └── openai_client.py      # fallback OpenAI Realtime
└── tools/
    └── registry.py           # déclarations d'outils
```

### 2.3 Détail du `ToolDispatcher`

```python
# jarvis/core/tool_dispatcher.py
from typing import Callable, Awaitable
from actions import (
    open_app, web_search, weather_action, send_message, reminder,
    youtube_video, screen_process, computer_settings, browser_control,
    file_controller, desktop_control, code_helper, dev_agent,
    computer_control, game_updater, flight_finder, file_processor,
)

_TOOL_REGISTRY: dict[str, Callable[..., Awaitable[str]]] = {
    "open_app": open_app,
    "web_search": web_search,
    # ...
}
```

Chaque action devrait être adaptée pour recevoir un `Player` protocol au lieu de `JarvisUI`.

## 3. Découpage recommandé de `ui.py`

`ui.py` fait 1800 lignes. Il contient :

- Constantes de couleurs (`C`)
- Helpers de couleur (`qcol`)
- `_SysMetrics` (métriques système)
- `HudCanvas` (animation HUD)
- `MetricBar`, `LogWidget`, `FileDropZone`, `_DropCanvas`
- `SetupOverlay`, `RemoteKeyOverlay`
- `JarvisUI` (fenêtre principale)
- `JarvisApp` (wrapper QApplication)

### 3.1 Modules à extraire de `ui.py`

| Module cible | Contenu extrait | Lignes concernées |
|---|---|---|
| `jarvis/ui/constants.py` | Classe `C`, `qcol()`, dimensions | `ui.py:48-73`, `ui.py:40-43` |
| `jarvis/ui/metrics.py` | `_SysMetrics` | `ui.py:75-243` |
| `jarvis/ui/hud_canvas.py` | `HudCanvas` | `ui.py:245-503` |
| `jarvis/ui/metric_bar.py` | `MetricBar` | `ui.py:503-556` |
| `jarvis/ui/log_widget.py` | `LogWidget` | `ui.py:557-642` |
| `jarvis/ui/file_drop.py` | `FileDropZone`, `_DropCanvas`, icônes | `ui.py:643-857` |
| `jarvis/ui/setup_overlay.py` | `SetupOverlay` | `ui.py:858-984` |
| `jarvis/ui/remote_overlay.py` | `RemoteKeyOverlay` | `ui.py:987-1150` |
| `jarvis/ui/main_window.py` | `JarvisUI` (fenêtre principale) | `ui.py:1151-1800` |
| `jarvis/ui/app.py` | `JarvisApp` | `ui.py:1736-1743` |

### 3.2 Architecture cible de l'UI

```
jarvis/ui/
├── __init__.py
├── constants.py
├── metrics.py
├── hud_canvas.py
├── metric_bar.py
├── log_widget.py
├── file_drop.py
├── setup_overlay.py
├── remote_overlay.py
├── main_window.py
└── app.py
```

### 3.3 Protocole `Player` pour découpler UI/actions

```python
# jarvis/core/player.py
from typing import Protocol, runtime_checkable

@runtime_checkable
class Player(Protocol):
    def write_log(self, text: str) -> None: ...
    def set_state(self, state: str) -> None: ...
    @property
    def muted(self) -> bool: ...
    @property
    def current_file(self) -> str | None: ...
```

`JarvisUI` implémentera `Player`. Les tests utiliseront un `FakePlayer`.

## 4. Modules à créer

### 4.1 Modules de sécurité

| Module | Rôle | Remplace |
|---|---|---|
| `jarvis/security/secrets.py` | Gestion des secrets via keyring / env | `memory/config_manager.py` |
| `jarvis/security/crypto.py` | Chiffrement AES-GCM avec PBKDF2 | `dashboard/server.py:72-90` |
| `jarvis/security/certs.py` | Génération de certificats auto-signés | `config/certs/` |
| `jarvis/security/sandbox.py` | Sandbox pour exécution de code (ou suppression) | `actions/desktop.py:83-101` |
| `jarvis/security/permissions.py` | Validation des actions sensibles | Partout |

### 4.2 Modules LLM

| Module | Rôle | Remplace |
|---|---|---|
| `jarvis/llm/client.py` | Interface `LLMClient` | `core/llm_client.py` (partiel) |
| `jarvis/llm/gemini_client.py` | Implémentation Gemini Live | `main.py` (partie LLM) |
| `jarvis/llm/openai_client.py` | Fallback OpenAI Realtime | Nouveau |
| `jarvis/llm/router.py` | Routing multi-modèles | Nouveau |

### 4.3 Modules mémoire

| Module | Rôle | Remplace |
|---|---|---|
| `jarvis/memory/store.py` | Interface de stockage | `memory/memory_manager.py` |
| `jarvis/memory/json_store.py` | Implémentation JSON | `memory/memory_manager.py` |
| `jarvis/memory/vector_store.py` | Implémentation vectorielle | Nouveau |
| `jarvis/memory/embeddings.py` | Génération d'embeddings | Nouveau |

### 4.4 Modules web

| Module | Rôle | Remplace |
|---|---|---|
| `jarvis/web/server.py` | Point d'entrée FastAPI | `dashboard/server.py` |
| `jarvis/web/auth.py` | Authentification et tokens | `dashboard/server.py:391-500` |
| `jarvis/web/routes/commands.py` | Routes commandes | `dashboard/server.py` |
| `jarvis/web/routes/uploads.py` | Routes uploads | `dashboard/server.py:642-721` |
| `jarvis/web/routes/ws.py` | WebSocket | `dashboard/server.py` |
| `jarvis/web/crypto_endpoint.py` | Chiffrement messages | `dashboard/server.py` |
| `jarvis/web/firewall.py` | Configuration firewall | `dashboard/server.py:99-232` |

### 4.5 Modules audio

| Module | Rôle | Remplace |
|---|---|---|
| `jarvis/audio/capture.py` | Capture micro | `main.py:704-731` |
| `jarvis/audio/playback.py` | Lecture audio | `main.py:733-834` |
| `jarvis/audio/phone_relay.py` | Relai téléphone | `main.py:836-853` |

### 4.6 Modules de configuration

| Module | Rôle | Remplace |
|---|---|---|
| `jarvis/config/__init__.py` | Package config | `config/__init__.py` |
| `jarvis/config/paths.py` | Chemins | 11 implémentations de `get_base_dir` |
| `jarvis/config/keys.py` | Clés API | `memory/config_manager.py` |
| `jarvis/config/settings.py` | Settings type-safe (pydantic) | Configuration dispersée |

## 5. Plan de refactoring par phases

### Phase 1 — Fondations (2-3 semaines)

| # | Tâche | Fichier(s) | Effort |
|---|---|---|---|
| 1.1 | Créer `pyproject.toml` et `uv.lock` | Racine | Faible |
| 1.2 | Centraliser `get_base_dir` dans `jarvis/config/paths.py` | Tous les modules | Moyen |
| 1.3 | Centraliser la lecture de clé API | `memory/config_manager.py`, `actions/*.py` | Moyen |
| 1.4 | Introduire `Player` protocol | `jarvis/core/player.py`, `actions/*.py` | Moyen |
| 1.5 | Remplacer les `print()` par un logger structuré | Tous | Moyen |

### Phase 2 — Sécurité critique (2-3 semaines)

| # | Tâche | Fichier(s) | Effort |
|---|---|---|---|
| 2.1 | Supprimer `exec()` dans `actions/desktop.py` | `actions/desktop.py` | Important |
| 2.2 | Supprimer les `shell=True` | `actions/open_app.py`, `dashboard/server.py`, etc. | Moyen |
| 2.3 | Générer les certificats à la volée | `config/certs/`, `dashboard/server.py` | Moyen |
| 2.4 | Chiffrer `api_keys.json` avec keyring | `memory/config_manager.py` | Moyen |
| 2.5 | Renforcer l'authentification dashboard | `dashboard/server.py` | Moyen |

### Phase 3 — Découpage `main.py` (3-4 semaines)

| # | Tâche | Fichier(s) | Effort |
|---|---|---|---|
| 3.1 | Extraire les constantes audio | `main.py:46-50` | Faible |
| 3.2 | Extraire le registre d'outils | `main.py:74-466` | Moyen |
| 3.3 | Extraire le dispatcher | `main.py:571-697` | Moyen |
| 3.4 | Extraire l'orchestrateur | `main.py:471-560`, `890-953` | Important |
| 3.5 | Extraire l'audio (capture, playback, relay) | `main.py:704-853` | Moyen |
| 3.6 | Extraire le connector dashboard | `main.py:855-887` | Moyen |

### Phase 4 — Découpage `ui.py` (3-4 semaines)

| # | Tâche | Fichier(s) | Effort |
|---|---|---|---|
| 4.1 | Extraire les constantes et helpers | `ui.py:48-73` | Faible |
| 4.2 | Extraire `_SysMetrics` | `ui.py:75-243` | Faible |
| 4.3 | Extraire `HudCanvas` | `ui.py:245-503` | Moyen |
| 4.4 | Extraire les widgets (MetricBar, LogWidget, FileDropZone) | `ui.py:503-857` | Moyen |
| 4.5 | Extraire les overlays | `ui.py:858-1150` | Moyen |
| 4.6 | Extraire `JarvisUI` et `JarvisApp` | `ui.py:1151-1800` | Moyen |

### Phase 5 — Abstraction LLM (2-3 semaines)

| # | Tâche | Fichier(s) | Effort |
|---|---|---|---|
| 5.1 | Créer l'interface `LLMClient` | `jarvis/llm/client.py` | Faible |
| 5.2 | Migrer `core/llm_client.py` vers `jarvis/llm/ollama_client.py` | `core/llm_client.py` | Moyen |
| 5.3 | Créer `GeminiLiveClient` | `main.py` (partie LLM) | Moyen |
| 5.4 | Créer `OpenAIRealtimeClient` | Nouveau | Moyen |
| 5.5 | Créer le router | `jarvis/llm/router.py` | Moyen |

### Phase 6 — Mémoire et persistance (2-3 semaines)

| # | Tâche | Fichier(s) | Effort |
|---|---|---|---|
| 6.1 | Déplacer données utilisateur avec `platformdirs` | `memory/*` | Faible |
| 6.2 | Remplacer JSON par SQLite | `memory/memory_manager.py` | Moyen |
| 6.3 | Ajouter une interface de stockage | `jarvis/memory/store.py` | Moyen |
| 6.4 | Ajouter embeddings et recherche sémantique | `jarvis/memory/vector_store.py` | Important |

### Phase 7 — Tests et qualité (2-3 semaines)

| # | Tâche | Fichier(s) | Effort |
|---|---|---|---|
| 7.1 | Créer `tests/` avec tests unitaires | Nouveau | Moyen |
| 7.2 | Ajouter `pytest` + fixtures | `pyproject.toml` | Faible |
| 7.3 | Mock PyAutoGUI, Playwright, subprocess | `tests/` | Moyen |
| 7.4 | Ajouter tests d'intégration audio | `tests/audio/` | Moyen |
| 7.5 | Configurer CI/CD GitHub Actions | `.github/workflows/` | Faible |

### Phase 8 — DevOps et packaging (2-3 semaines)

| # | Tâche | Fichier(s) | Effort |
|---|---|---|---|
| 8.1 | Dockeriser le dashboard | `Dockerfile.dashboard` | Moyen |
| 8.2 | Dockeriser le core headless | `Dockerfile.core` | Moyen |
| 8.3 | Ajouter `docker-compose.yml` | Racine | Faible |
| 8.4 | Ajouter health checks | `jarvis/web/server.py` | Faible |
| 8.5 | Ajouter monitoring OpenTelemetry | `jarvis/observability/` | Moyen |

## 6. Estimation d'effort totale

| Phase | Durée | Livrable clé |
|---|---|---|
| Phase 1 — Fondations | 2-3 semaines | `pyproject.toml`, `Player` protocol, logger |
| Phase 2 — Sécurité critique | 2-3 semaines | RCE supprimé, certificats générés, clés chiffrées |
| Phase 3 — Découpage `main.py` | 3-4 semaines | `jarvis/core/`, `jarvis/audio/`, `jarvis/tools/` |
| Phase 4 — Découpage `ui.py` | 3-4 semaines | `jarvis/ui/` |
| Phase 5 — Abstraction LLM | 2-3 semaines | `jarvis/llm/` |
| Phase 6 — Mémoire | 2-3 semaines | `jarvis/memory/` SQLite + vectoriel |
| Phase 7 — Tests | 2-3 semaines | Suite de tests + CI/CD |
| Phase 8 — DevOps | 2-3 semaines | Docker, monitoring |
| **Total** | **18-26 semaines** | Version refactorisée et industrialisée |

## 7. Ordre de priorité

1. **P0 — Sécurité** : RCE, `shell=True`, clés commitées. Bloquant pour toute production.
2. **P1 — Fondations** : `pyproject.toml`, `Player` protocol, centralisation config.
3. **P1 — Découpage `main.py`** : le plus gros impact sur la maintenabilité.
4. **P2 — Découpage `ui.py`** : améliore la testabilité et la lisibilité.
5. **P2 — Abstraction LLM** : prépare le multi-fournisseur.
6. **P3 — Mémoire vectorielle** : améliore l'expérience utilisateur.
7. **P3 — DevOps** : Docker, CI/CD, monitoring.

## 8. Risques du refactoring

| Risque | Mitigation |
|---|---|
| Régression fonctionnelle | Tests avant/après, refactoring incrémental |
| Perte de la signature des actions | Garder la signature `parameters, response, player, session_memory` pendant la transition |
| Complexité du multi-modèle | Garder Gemini par défaut, ajouter progressivement |
| Performance audio dégradée | Benchmarks latence avant/après |
| UI lente après découpage | Qt signals/slots bien isolés |

## 9. Conclusion

Le refactoring de MARK XLVI est **ambitieux mais nécessaire**. Une approche incrémentale par phases permet de livrer de la valeur à chaque étape sans tout casser. La priorité absolue est la sécurité, puis le découpage de `main.py` qui est le principal point de rupture architectural.

## 10. Citations clés

- `main.py` : `main.py:1-969`
- `ui.py` : `ui.py:1-1800`
- `dashboard/server.py` : `dashboard/server.py:1-795`
- `actions/desktop.py` RCE : `actions/desktop.py:83-101`
- `actions/open_app.py` shell : `actions/open_app.py:83-99`
- `config/certs/jarvis.key` : clé privée commitée
- `memory/memory_manager.py` : mémoire JSON tronquée
- `core/llm_client.py` : client Ollama non utilisé
