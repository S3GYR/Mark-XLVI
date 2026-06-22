# Revue DevOps — MARK XLVI

> Ce document évalue la préparation de MARK XLVI à être déployé, maintenu et opéré en production quotidienne, sous les angles installation, dépendances, conteneurisation, orchestration, CI/CD et monitoring.

## 1. Analyse de l'installation

### 1.1 Procédure actuelle

Le README recommande :

```@c:\Users\yoann\devin\Mark\Mark-XLVI\readme.md:45-54
```bash
git clone https://github.com/FatihMakes/Mark-XLVI.git
cd Mark-XLVI
pip install -r requirements.txt
playwright install
python main.py
```
```

> **Note d'installation** : certaines dépendances spécifiques au système d'exploitation ne sont pas dans `requirements.txt`.

### 1.2 Script setup.py

`setup.py` automatise l'installation :

```@c:\Users\yoann\devin\Mark\Mark-XLVI\setup.py:1-12
import subprocess
import sys

print("Installing requirements...")
subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)

print("Installing Playwright browsers...")
subprocess.run([sys.executable, "-m", "playwright", "install"], check=True)

print("\n✅ Setup complete! Run 'python main.py' to start MARK XXV.")
```

### 1.3 Problèmes d'installation

| Problème | Impact |
|---|---|
| `setup.py` utilise `subprocess.run` sans isolation | Modifie l'environnement Python global |
| Pas de virtualenv/conda recommandé | Conflits de dépendances possibles |
| Dépendances non versionnées | Builds non reproductibles |
| Dépendances optionnelles absentes | Échecs au premier lancement si le réseau est indisponible |
| `playwright install` télécharge des navigateurs | ~150 Mo, nécessite un accès réseau |
| Installation des dépendances Windows (`win10toast`, `pywinauto`, etc.) conditionnelles | Fonctionne mal sur macOS/Linux si mal géré |
| Pas de fichier `.env` | Configuration uniquement interactive via l'UI |

### 1.4 Recommandations d'installation

- Remplacer `setup.py` par un `pyproject.toml` standard avec groupes d'extras.
- Fournir un `uv.lock` ou `requirements.lock` figé.
- Documenter l'utilisation d'un environnement virtuel.
- Séparer l'installation des dépendances optionnelles (TTS, STT, vision, dashboard).
- Fournir un script de vérification post-install (`python -m jarvis.doctor`).

## 2. Analyse des dépendances

### 2.1 Dépendances de base

`requirements.txt` contient 28 paquets sans version :

```@c:\Users\yoann\devin\Mark\Mark-XLVI\requirements.txt:1-28
sounddevice
google-genai
google-generativeai
pillow
requests
beautifulsoup4
duckduckgo-search
playwright
pyautogui
pyperclip
pygetwindow
opencv-python
numpy
mss
psutil
send2trash
youtube-transcript-api
python-pptx
fastapi
uvicorn[standard]
cryptography
python-multipart
comtypes; sys_platform == "win32"
pycaw; sys_platform == "win32"
win10toast; sys_platform == "win32"
pywinauto; sys_platform == "win32"
qrcode[pil]
```

### 2.2 Dépendances optionnelles non déclarées

Plusieurs modules importent des paquets absents de `requirements.txt` :

| Module | Dépendance manquante | Usage |
|---|---|---|
| `core/stt.py` | `faster-whisper`, `vosk` | Speech-to-Text |
| `core/tts.py` | `edge-tts`, `kokoro`, `soundfile`, `miniaudio` | Text-to-Speech |
| `actions/file_processor.py` | `pandas`, `openpyxl`, `python-docx`, `pydub` | Traitement de fichiers |
| `core/tts.py` (Kokoro) | `torch` | GPU/CPU inference |
| `dashboard/server.py` | `fastapi`, `uvicorn`, `cryptography`, `python-multipart` | Déjà listées, mais pas en groupes |

Ces dépendances sont installées à la volée par `core/installer.py` ou signalées par des messages d'erreur.

### 2.3 Conflits potentiels

- `google-genai` et `google-generativeai` : deux SDK pour le même service. Le code utilise `google-genai`, mais les deux sont installés.
- `pyautogui` + `pywinauto` + `pygetwindow` : trois bibliothèques d'automatisation GUI avec des approches différentes.
- `uvicorn[standard]` inclut `httptools`, `uvloop`, `websockets` : ok pour FastAPI.
- `numpy` + `opencv-python` + `mss` + `pillow` : redondance possible dans le traitement d'images.

### 2.4 Proposition de regroupement

```toml
[project]
dependencies = [
    "sounddevice",
    "google-genai>=0.5",
    "pillow",
    "requests",
    "beautifulsoup4",
    "duckduckgo-search",
    "psutil",
    "send2trash",
    "qrcode[pil]",
]

[project.optional-dependencies]
dashboard = ["fastapi", "uvicorn[standard]", "cryptography", "python-multipart"]
tts = ["edge-tts", "kokoro>=0.9", "soundfile", "miniaudio"]
stt = ["faster-whisper", "vosk"]
vision = ["opencv-python", "mss"]
windows = ["comtypes", "pycaw", "win10toast", "pywinauto", "pygetwindow"]
files = ["pandas", "openpyxl", "python-docx", "pydub", "youtube-transcript-api", "python-pptx"]
```

## 3. Dockerisation possible

### 3.1 Faisabilité

**Partielle et complexe.** MARK XLVI n'est pas nativement conçu pour Docker pour les raisons suivantes :

- **Interface graphique PyQt6** : Qt nécessite un serveur X11 ou Wayland. Dockeriser une GUI desktop est possible avec `X11 forwarding`, `VNC`, ou `noVNC`, mais cela ajoute de la complexité.
- **Audio** : `sounddevice` accède aux périphériques audio ALSA/PulseAudio/Jack. En conteneur, il faut mapper `/dev/snd`, `/dev/dsp`, ou utiliser PulseAudio via socket.
- **Playwright** : nécessite Chromium/Chrome. Il est possible d'utiliser l'image Playwright officielle, mais la taille augmente (~1 Go).
- **PyAutoGUI** : simule clavier/souris au niveau du système. Dans un conteneur, il n'a pas accès au display host sans X11 forwarding.
- **Webcam** : `opencv-python` accède à `/dev/video0`. Mapping nécessaire.
- **Élévation de privilèges** : le firewall et certaines actions système nécessitent `CAP_NET_ADMIN` ou un `--privileged`, ce qui rompt l'isolation Docker.

### 3.2 Dockerfile recommandé (architecture)

```dockerfile
FROM mcr.microsoft.com/playwright/python:v1.46.0-jammy

# Dépendances système
RUN apt-get update && apt-get install -y \
    libportaudio2 libasound2-dev libpulse-dev \
    libqt6widgets6 libxkbcommon-x11-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml .
RUN pip install -e ".[dashboard,tts,stt,vision,files]"

# Playwright browsers
RUN playwright install chromium

COPY . .

EXPOSE 8000
CMD ["python", "main.py"]
```

> Ce Dockerfile est indicatif. Il ne résout pas les problèmes d'audio, de GUI et de privilèges.

### 3.3 Stratégie de conteneurisation

- **Option A** : Conteneuriser uniquement le **dashboard web** (`dashboard/server.py`). C'est la partie la plus facile à isoler car elle est déjà en FastAPI.
- **Option B** : Conteneuriser le **core** sans UI (mode headless + API REST). Nécessite de découpler `main.py` de `ui.py`.
- **Option C** : Conteneuriser l'application complète avec VNC/noVNC. Lourde, complexe, mais fonctionnelle pour un usage local.

**Recommandation** : Option A puis Option B après refactoring.

## 4. Kubernetes readiness

### 4.1 État actuel

MARK XLVI n'est **pas Kubernetes-ready**.

- **Stateful** : mémoire, tokens, clés AES, session Gemini sont en mémoire locale. Un pod redémarré perd tout.
- **Singleton** : une seule session par processus. Pas de réplication horizontale.
- **Stockage local** : fichiers uploadés, mémoire JSON, certificats sont sur disque local. Pas de PVC défini.
- **GUI** : impossible à déployer nativement dans Kubernetes.
- **Audio** : accès aux périphériques physiques incompatible avec Kubernetes classique.
- **Secrets** : clés API et certificats en clair dans le filesystem.

### 4.2 Prérequis pour Kubernetes

Pour rendre MARK XLVI compatible Kubernetes, il faudrait :

1. **Séparer le backend API** du frontend desktop.
2. **Externaliser l'état** : Redis pour les sessions, PostgreSQL/SQLite pour la mémoire, S3/MinIO pour les uploads.
3. **Gérer les secrets** via Kubernetes Secrets ou un vault externe.
4. **Supprimer la dépendance au hardware audio** (utiliser WebRTC côté client).
5. **Supprimer PyAutoGUI** pour les actions système (incompatible avec un conteneur).
6. **Ajouter des health checks** (`/health`, `/ready`) au serveur FastAPI.
7. **Définir des ressources** : limites CPU/mémoire pour éviter qu'un LLM ne sature le node.
8. **Utiliser un Ingress** avec TLS terminé (Let's Encrypt) plutôt que les certificats commités.

### 4.3 Verdict Kubernetes

| Critère | État |
|---|---|
| Stateless | ❌ Non |
| Configurable via variables d'environnement | ❌ Non |
| Health checks | ❌ Non |
| Sécrets externalisés | ❌ Non |
| Stockage partagé | ❌ Non |
| Horizontal scalability | ❌ Non |
| GUI headless | ❌ Non |
| Networking sécurisé | ❌ Non |

**Conclusion** : Kubernetes n'est pas adapté dans l'état actuel. Un refactoring majeur est nécessaire.

## 5. CI/CD recommandé

### 5.1 Pipeline GitHub Actions proposée

```yaml
name: CI

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv run ruff check .
      - run: uv run ruff format --check .
      - run: uv run mypy jarvis/

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync --extra dashboard,tts,stt,vision,files
      - run: uv run pytest --cov=jarvis --cov-report=xml
      - uses: codecov/codecov-action@v4

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install pip-audit bandit
      - run: pip-audit -r requirements.txt
      - run: bandit -r jarvis/

  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv build
```

### 5.2 Livrables CI/CD recommandés

- **Lint** : `ruff` ou `flake8` + `black`/`ruff format`.
- **Type checking** : `mypy` ou `pyright`.
- **Tests** : `pytest` avec `pytest-asyncio`, `pytest-qt` pour l'UI.
- **Sécurité** : `bandit`, `pip-audit`, `trivy`.
- **Packaging** : `uv build` ou `python -m build`.
- **Release** : GitHub Release avec binaires PyInstaller optionnels.

## 6. Monitoring recommandé

### 6.1 Métriques à collecter

| Métrique | Outil suggéré | Pourquoi |
|---|---|---|
| Latence Gemini Live | Prometheus + Grafana | Qualité de l'expérience vocale |
| Nombre de tool calls | Prometheus | Usage et coût |
| Temps d'exécution des actions | OpenTelemetry | Identifier les actions lentes |
| Erreurs par action | Sentry / Loki | Débogage |
| Utilisation CPU/RAM/GPU | Prometheus node exporter | Capacité du poste |
| Coût API | Export Prometheus custom | Maîtrise budgétaire |
| Temps de réponse dashboard | FastAPI middleware + Prometheus | SLA |
| File audio | Métrique custom | Détection de backpressure |

### 6.2 Logging structuré

Remplacer les `print()` par un logger structuré (`structlog` ou `logging` JSON) avec contexte :

```json
{
  "timestamp": "2026-06-21T11:28:00Z",
  "level": "INFO",
  "component": "tool_dispatcher",
  "tool": "browser_control",
  "duration_ms": 2450,
  "status": "success"
}
```

### 6.3 Tracing

Utiliser **OpenTelemetry** pour tracer les sessions Gemini, les appels d'outils, et les requêtes dashboard. Cela permet de comprendre la latence bout-en-bout.

### 6.4 Alerting

- Alertes sur erreurs de connexion Gemini répétées.
- Alertes sur utilisation CPU/RAM > 80%.
- Alertes sur échecs d'authentification dashboard.
- Alertes sur coût API dépassant un seuil.

## 7. Verdict DevOps

| Critère | État | Recommandation | Priorité |
|---|---|---|---|
| Installation reproductible | ❌ | `pyproject.toml` + lock | Haute |
| Dépendances versionnées | ❌ | `requirements.lock` + extras | Haute |
| Dockerisation | ⚠️ | Dashboard d'abord, puis core headless | Moyenne |
| Kubernetes | ❌ | Refactoring majeur requis | Basse |
| CI/CD | ❌ | GitHub Actions lint/test/security | Haute |
| Monitoring | ❌ | OpenTelemetry + Prometheus | Moyenne |
| Logging | ❌ | Logging structuré | Moyenne |
| Secrets management | ❌ | Vault / keyring / K8s Secrets | Haute |
| Health checks | ❌ | Endpoints `/health`, `/ready` | Moyenne |

## 8. Citations clés

- Procédure installation : `readme.md:45-54`
- `setup.py` : `setup.py:1-12`
- `requirements.txt` : `requirements.txt:1-28`
- Auto-installation dépendances : `core/installer.py:68-82`, `core/tts.py:170-175`
- Dépendances manquantes : `actions/file_processor.py`, `core/stt.py`, `core/tts.py`
- Dashboard : `dashboard/server.py:1-795`
- Configuration stockée localement : `memory/config_manager.py:10-12`, `memory/memory_manager.py:14-15`
- Certificats commités : `config/certs/jarvis.key`, `config/certs/jarvis.crt`
