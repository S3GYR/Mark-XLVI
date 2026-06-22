# Revue d'architecture — MARK XLVI

> Audit d'architecture de niveau expert, avec un regard d'architecte logiciel, DevOps, cybersécurité et IA. Ce document évalue la capacité du projet à être utilisé en production quotidienne.

## 1. Forces de l'architecture

- **Découpage fonctionnel par actions** : chaque domaine (navigateur, fichiers, système, météo, etc.) est isolé dans un module de `actions/`. La signature homogène `fonction(parameters, response, player, session_memory)` simplifie l'ajout d'un nouvel outil.
- **Intégration audio native** : le pipeline `sd.InputStream` → Gemini Live → `sd.RawOutputStream` est cohérent et exploitant le modèle `gemini-2.5-flash-native-audio-preview` (`main.py:46`, `main.py:704-834`).
- **Dashboard web complet** : FastAPI + WebSocket + QR code + upload de fichiers + audio téléphone offre une expérience de contrôle à distance aboutie pour un projet personnel (`dashboard/server.py`).
- **Support multi-OS** : le code gère Windows, macOS et Linux avec des branches conditionnelles explicites (`actions/browser_control.py`, `actions/computer_settings.py`, `actions/desktop.py`).
- **Moteur TTS/STT interchangeable** : `core/tts.py` supporte EdgeTTS, Kokoro et ElevenLabs ; `core/stt.py` supporte Whisper et Vosk. Cela permet d'adapter l'assistant à différents environnements (offline, cloud, GPU).
- **Mémoire structurée** : la mémoire long terme est catégorisée (`identity`, `preferences`, `projects`, `relationships`, `wishes`, `notes`) et injectée dans le prompt système (`memory/memory_manager.py`, `main.py:535-569`).

## 2. Faiblesses de l'architecture

- **Monolithe central surchargé** : `main.py` mélange orchestration Gemini, déclarations d'outils, exécution d'outils, audio I/O, dashboard et gestion d'état UI.
- **Interface graphique monolithique** : `ui.py` (1800 lignes) concentre HUD, peinture, log, drop de fichiers, setup, métriques, QR code.
- **Serveur web surchargé** : `dashboard/server.py` gère routes, firewall, chiffrement, auth, uploads, WebSocket et relai audio.
- **Deux clients LLM sans abstraction** : `main.py` utilise `google-genai` ; `core/llm_client.py` implémente Ollama/OpenAI mais n'est pas branché au core.
- **Stockage des données dans le répertoire source** : configuration et mémoire sont écrites à côté du code (`config/api_keys.json`, `memory/long_term.json`), ce qui interdit un packaging propre.
- **Absence de tests et d'outils de qualité** : pas de `tests/`, pas de CI/CD, pas de linting configuré.

## 3. Architecture globale

L'application adopte une architecture **monolithique modulaire** : un noyau central (`main.py`) orchestre une interface graphique PyQt6, une session audio temps réel avec Gemini, et un serveur web FastAPI. Les actions système sont découpées dans `actions/`, mais elles sont toutes invoquées par un même dispatcher synchrone/asynchrone dans `main.py`.

### Schéma conceptuel

```
┌─────────────────────────────────────────────┐
│                 ui.py (PyQt6)               │
│  HUD · Log · Drop fichiers · Setup · QR     │
└───────────────────┬─────────────────────────┘
                    │
┌───────────────────▼─────────────────────────┐
│                main.py (JarvisLive)         │
│   Gemini Live · Tool dispatcher · Audio I/O │
│   Dashboard integration · Phone relay       │
└───────┬───────────────┬───────────────┬─────┘
        │               │               │
┌───────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
│   actions/   │ │   core/     │ │ dashboard/  │
│   outils LLM │ │   stt/tts/  │ │   web + WS  │
│   exécution  │ │   llm/inst  │ │   mobile    │
└──────────────┘ └─────────────┘ └─────────────┘
        │
┌───────▼──────┐
│   memory/    │
│  JSON perso  │
└──────────────┘
```

## 3. Points de rupture

Un point de rupture est un composant dont la défaillance paralyse tout ou partie du système. MARK XLVI en présente plusieurs :

- **Session Gemini Live unique** : `main.py` maintient une seule `session` (`main.py:475`). Si la connexion réseau est instable, l'ensemble de l'interaction vocale s'arrête. La reconnexion automatique est en boucle fixe (`main.py:939-952`), ce qui peut masquer une erreur persistante sans jamais récupérer proprement.
- **Thread UI principal** : `ui.py` exécute `QApplication.exec()` dans le thread principal (`main.py:966`). Tout blocage long dans une action (build, flight, upload) fige l'interface.
- **Audio I/O dans l'event loop** : `_listen_audio` et `_play_audio` dépendent de `sounddevice` et de la file `asyncio.Queue`. Un plantage du pilote audio ou un délai réseau bloque la boucle.
- **Dashboard stateful** : les tokens, clés AES et historique sont en mémoire (`dashboard/server.py:373-384`). Un redémarrage du processus invalide toutes les sessions téléphone.
- **Stockage JSON de la mémoire** : `memory/long_term.json` est la source unique de vérité. Sa corruption ou sa suppression efface toute la mémoire long terme sans backup.
- **Dépendance à `pyautogui` pour les actions système** : `actions/computer_control.py`, `actions/send_message.py`, `actions/computer_settings.py` reposent sur PyAutoGUI. Si le focus fenêtre change ou si l'application cible est inaccessible, l'action échoue sans recours.
- **Dépendance à Playwright pour le navigateur** : `actions/browser_control.py` maintient un contexte par navigateur en mémoire. Un crash de Chromium ou un profil verrouillé invalide toute la session navigateur.

## 4. Maintenabilité

### 4.1 Taille et responsabilités des fichiers

- `main.py` (969 lignes, 45 Ko) : orchestration, déclarations d'outils, exécution, audio, dashboard. **Responsabilités multiples**.
- `ui.py` (1800 lignes, 68 Ko) : toute l'interface graphique, la peinture HUD, le setup, les métriques, le drop de fichiers. **Fichier surchargé**.
- `dashboard/server.py` (795 lignes, 35 Ko) : serveur web, firewall, chiffrement, uploads, WebSocket. **Trop de rôles**.
- `actions/browser_control.py` (893 lignes, 35 Ko) : logique complexe de Playwright multi-OS.

**Impact** : la difficulté de test, de revue et de modification est élevée. Une modification de la logique d'affichage peut impacter l'audio, etc.

### 4.2 Duplication de code

La fonction `get_base_dir()` est réimplémentée presque à l'identique dans :

- `main.py:37-40`
- `core/llm_client.py:33-36`
- `memory/config_manager.py:5-8`
- `memory/memory_manager.py:8-11`
- `config/__init__.py` (utilise `Path(__file__).parent`)
- `ui.py:31-34`
- `actions/web_search.py:6-9`
- `actions/desktop.py:21-24`
- `actions/computer_control.py:27-30`
- `actions/code_helper.py:9-12`
- `actions/dev_agent.py:9-12`
- `actions/send_message.py:21-24`

Autre duplication : chaque module `actions/*.py` relit `config/api_keys.json` avec son propre `_get_api_key()` (`actions/web_search.py:16-18`, `actions/desktop.py:26-29`, `actions/code_helper.py:21-23`, `actions/dev_agent.py:22-24`).

### 4.3 Cohérence des signatures

Toutes les actions partagent une signature commune, ce qui est un point positif. Cependant, certains modules reçoivent `response` et `session_memory` sans jamais les utiliser (`actions/weather_report.py`, `actions/send_message.py`), ce qui crée du bruit.

## 5. Scalabilité

### 5.1 Contraintes de scalabilité

- **Session unique** : `main.py` gère une seule session Gemini Live à la fois. Pas de multi-utilisateur, pas de file de jobs.
- **Mémoire en RAM** : tokens d'authentification, clés AES, historique WebSocket sont stockés en mémoire (`dashboard/server.py:373-384`). Le redémarrage du processus invalide toutes les sessions.
- **Mémoire long terme limitée** : `MEMORY_MAX_CHARS = 2200` (`memory/memory_manager.py:18`). Elle est tronquée silencieusement si elle dépasse la taille, avec perte d'informations.
- **File d'upload limitée** : `MAX_UPLOAD_MB = 500` (`dashboard/server.py:41`), mais le fichier est écrit synchronement sur disque pendant l'upload.

### 5.2 Gestion audio

- Les files `audio_in_queue` et `out_queue` sont recréées à chaque reconnexion (`main.py:921-922`), ce qui est correct, mais le streaming audio est entièrement dépendant de la latence réseau Gemini.
- `CHUNK_SIZE = 1024` et `SEND_SAMPLE_RATE = 16000` sont des constantes fixes, non configurables sans modifier le code.

## 6. Couplages excessifs

### 6.1 Couplage UI ↔ Logique métier

`main.py` dépend directement de `JarvisUI` (`main.py:13`, `main.py:954`). Toute exécution d'outil appelle `self.ui.set_state`, `self.ui.write_log`, `self.ui.muted`, etc. Cela empêche d'utiliser le core sans l'interface graphique.

### 6.2 Couplage actions ↔ UI

Chaque action reçoit un `player` qui est en réalité l'instance UI (`JarvisUI`). Le module écrit directement dans le log et déclenche des effets de bord visuels. Exemples :

```
actions/web_search.py:116      player.write_log(...)
actions/desktop.py:434         player.write_log(...)
actions/computer_control.py    (nombreuses références)
```

Cela viole le principe d'inversion de dépendance et rend le test unitaire impossible sans monter l'UI.

### 6.3 Couplage au système de fichiers

La configuration (`api_keys.json`) et la mémoire (`long_term.json`) sont stockées dans le répertoire du projet. Cela empêche une installation système propre ou un packaging, et mélange code et données utilisateur.

### 6.4 Couplage aux SDK spécifiques

`main.py` importe directement `from google import genai` et `from google.genai import types`. `core/llm_client.py` implémente un autre client (Ollama/OpenAI) qui n'est **pas** utilisé par `main.py`. Il existe donc **deux clients LLM coexistants sans abstraction commune**.

## 7. Propositions d'amélioration architecturale

### 7.1 Séparation des responsabilités

| Responsabilité | Emplacement actuel | Proposition |
|---|---|---|
| Orchestration Gemini | `main.py` | `jarvis/core/orchestrator.py` |
| Déclarations d'outils | `main.py` | `jarvis/tools/registry.py` |
| Audio I/O | `main.py` | `jarvis/audio/` (capture, playback, phone relay) |
| Interface graphique | `ui.py` | `jarvis/ui/` (widgets, canvas, overlays) |
| Serveur web | `dashboard/server.py` | `jarvis/web/` (routes, auth, ws, upload) |
| Configuration | `memory/config_manager.py` + dispersée | `jarvis/config.py` unique |
| Client LLM | `main.py` + `core/llm_client.py` | `jarvis/llm/` avec abstraction unique |

### 7.2 Abstraction du client LLM

Créer une interface `LLMClient` commune, avec deux implémentations : `GeminiLiveClient` et `OllamaClient`. Le dispatcher d'outils ne devrait pas connaître le backend.

### 7.3 Bus d'événements / callbacks typés

Remplacer le `player` par un protocole minimal :

```python
class LogSink(Protocol):
    def write_log(self, text: str) -> None: ...
    def set_state(self, state: str) -> None: ...
```

Cela permettrait de brancher l'UI, un logger fichier, ou un test stub.

### 7.4 Stockage des données utilisateur

Déplacer la configuration et la mémoire dans un répertoire dédié, par exemple via `platformdirs` :

```python
from platformdirs import user_config_dir, user_data_dir
```

### 7.5 Tests et packaging

- Ajouter un `tests/` avec des tests unitaires sur les actions (mocker `player`, `subprocess`, `pyautogui`).
- Transformer `setup.py` en `pyproject.toml` standard.
- Séparer les dépendances optionnelles (groupes `[tts]`, `[stt]`, `[vision]`, `[dashboard]`).

## 8. Verdict architecture

| Critère | Note | Justification |
|---|---|---|
| Modularité | Moyenne | Découpage fonctionnel par action, mais monolithe central surchargé. |
| Maintenabilité | Moyenne/Faible | Fichiers trop longs, duplications, couplage UI/métier. |
| Testabilité | Faible | Impossible de tester les actions sans l'UI ou le réseau. |
| Scalabilité | Faible | Session unique, état en mémoire, mémoire tronquée. |
| Extensibilité | Moyenne | Ajout d'un outil relativement simple, mais deux backends LLM non unifiés. |
| Robustesse | Faible | Pas de gestion centralisée des erreurs, redémarrage global en boucle infinie. |
| Points de rupture | Faible | Session unique, state en mémoire, audio/UI dans le même thread. |
| Observabilité | Faible | Pas de logging structuré, pas de métriques exposées, pas de tracing. |

## 9. Testabilité

### 9.1 État actuel

La testabilité est **faible** pour plusieurs raisons :

- **Couplage direct à l'UI** : les actions reçoivent `player` qui est une instance concrète de `JarvisUI`. Il est impossible d'appeler une action sans monter l'interface PyQt6 (`actions/web_search.py:116`, `actions/desktop.py:434`).
- **Dépendances externes réelles** : `actions/computer_control.py` importe `pyautogui` au niveau module. Les tests unitaires doivent mocker la bibliothèque native ou accepter un échec si le système n'est pas disponible.
- **Appels réseau directs** : `actions/web_search.py` appelle `google.genai` et `duckduckgo_search` sans abstraction ni injection de dépendances.
- **Pas de tests existants** : aucun répertoire `tests/`, aucun `pytest.ini`, aucun fixture.
- **Dispatch asynchrone difficile à tester** : `main.py:571-697` exécute les outils dans `run_in_executor` sans sérialisation claire des résultats.

### 9.2 Améliorations nécessaires

- Définir un `LogSink` / `Player` protocol (interface) pour remplacer l'instance UI.
- Injecter les clients API (Gemini, DuckDuckGo) plutôt que de les instancier dans les modules.
- Utiliser `unittest.mock` ou `pytest-mock` pour `pyautogui`, `subprocess`, `playwright`.
- Créer des tests d'intégration audio sans réseau en mockant `genai.Client.aio.live.connect`.

## 10. Dette technique

La dette technique est détaillée dans `TECHNICAL_DEBT.md`. Les points les plus impactants pour l'architecture sont :

| # | Problème | Fichier | Impact architectural |
|---|---|---|---|
| 1 | Clé privée SSL commitée | `config/certs/jarvis.key` | Sécurité et confiance du dashboard compromise |
| 2 | RCE via `exec()` de code LLM | `actions/desktop.py:83-101` | Impossible à isoler ou tester sûrement |
| 3 | `shell=True` sur entrées utilisateur | `actions/open_app.py`, `dashboard/server.py` | Injection de commandes, non testable |
| 4 | Couplage UI/métier | `main.py:474-484`, `actions/*.py` | Monolithe, testabilité nulle |
| 5 | Deux clients LLM sans abstraction | `main.py`, `core/llm_client.py` | Redondance, confusion, maintenance double |
| 6 | `get_base_dir` dupliquée 11+ fois | multiples | Refactoring global nécessaire |
| 7 | Mémoire JSON tronquée | `memory/memory_manager.py:58-68` | Perte de données utilisateur |
| 8 | Dépendances non versionnées | `requirements.txt` | Builds non reproductibles |

## 11. Citations clés

- Déclaration des outils : `main.py:74-466`
- Dispatcher des outils : `main.py:571-697`
- Couplage UI : `main.py:474-484`
- Duplication `get_base_dir` : `main.py:37-40`, `core/llm_client.py:33-36`, `memory/config_manager.py:5-8`, `actions/desktop.py:21-24`, etc.
- Client Ollama non utilisé par `main.py` : `core/llm_client.py:1-587`
- Mémoire tronquée : `memory/memory_manager.py:58-68`
- Stockage config en clair : `memory/config_manager.py:20-35`
