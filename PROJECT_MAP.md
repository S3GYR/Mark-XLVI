# Cartographie du projet — MARK XLVI

> Audit réalisé sur le dépôt cloné. Toutes les citations renvoient au code effectivement analysé.

## 1. Vue d'ensemble

MARK XLVI est un assistant IA personnel, multi-plateforme (Windows, macOS, Linux), à interface vocale et graphique. Il se connecte en temps réel à l'API Gemini Live de Google, expose un dashboard web local pour le contrôle à distance par téléphone, et peut exécuter un grand nombre d'actions sur le poste de travail : contrôle du système, navigation web, gestion de fichiers, envoi de messages, recherche, etc.

- **Nom du projet** : MARK XLVI (JARVIS)
- **Auteur** : FatihMakes
- **Licence** : Creative Commons BY-NC 4.0 (usage personnel/non commercial)
- **Point d'entrée principal** : `main.py`
- **Interface graphique** : `ui.py` (PyQt6)

## 2. Arborescence des dossiers

```
c:\Users\yoann\devin\Mark\Mark-XLVI/
├── .git/                   # Dépôt Git
├── actions/                # Modules d'action (outils de l'agent)
│   ├── browser_control.py  # Contrôle de navigateurs via Playwright
│   ├── code_helper.py      # Génération/exécution de code
│   ├── computer_control.py # Contrôle clavier/souris bas niveau
│   ├── computer_settings.py # Réglages système (volume, luminosité, etc.)
│   ├── desktop.py          # Automatisation du bureau (fond d'écran, rangement)
│   ├── dev_agent.py        # Génération automatique de projets multi-fichiers
│   ├── file_controller.py  # Gestion de fichiers (CRUD, copie, déplacement)
│   ├── file_processor.py   # Traitement de fichiers uploadés (OCR, PDF, etc.)
│   ├── flight_finder.py    # Recherche de vols Google Flights
│   ├── game_updater.py     # Mise à jour de jeux Steam/Epic
│   ├── open_app.py         # Lancement d'applications
│   ├── reminder.py         # Rappels / planificateur
│   ├── screen_processor.py # Capture écran / webcam + analyse Gemini
│   ├── send_message.py     # Envoi de messages via WhatsApp, Telegram, etc.
│   ├── weather_report.py   # Météo (ouvre Google)
│   ├── web_search.py       # Recherche web (Gemini + DuckDuckGo)
│   └── youtube_video.py    # Contrôle YouTube
├── config/                 # Configuration + certificats SSL
│   ├── __init__.py         # Helpers OS
│   └── certs/
│       ├── jarvis.crt      # Certificat auto-signé (commité !)
│       └── jarvis.key      # Clé privée RSA (commitée !)
├── core/                   # Moteurs du core
│   ├── installer.py        # Installation automatique de dépendances
│   ├── llm_client.py       # Client Ollama / OpenAI-compatible
│   ├── prompt.txt          # Prompt système par défaut
│   ├── stt.py              # Speech-to-Text (Whisper/Vosk)
│   └── tts.py              # Text-to-Speech (EdgeTTS/Kokoro/ElevenLabs)
├── dashboard/              # Dashboard web / mobile
│   ├── server.py           # Serveur FastAPI + WebSocket
│   └── static/
│       ├── app.html        # Interface web principale
│       ├── crypto-js.min.js # CryptoJS (téléchargé puis servi)
│       └── login.html      # Page d'authentification
├── memory/                 # Mémoire persistante
│   ├── config_manager.py   # Gestion de api_keys.json
│   └── memory_manager.py  # Mémoire long terme JSON
├── main.py                 # Boucle principale Gemini Live + orchestration
├── ui.py                   # Interface PyQt6 + overlay setup
├── readme.md               # Documentation utilisateur
├── requirements.txt        # Dépendances de base
└── setup.py                # Script d'installation
```

## 3. Technologies utilisées

### 3.1 Langage & framework UI

- **Python 3.11/3.12** (préconisé dans le README)
- **PyQt6** pour l'interface de bureau (`ui.py:16-29`)

### 3.2 Intelligence artificielle

- **Google Gemini API** via le SDK `google-genai` (`main.py:11-12`, `main.py:893-896`)
- Modèle principal : `models/gemini-2.5-flash-native-audio-preview-12-2025` (`main.py:46`)
- Modèles secondaires : `gemini-2.5-flash` (`actions/web_search.py:26`, `actions/desktop.py:145`, `actions/code_helper.py:18`, `actions/dev_agent.py:19`)
- **Ollama** (optionnel) via `core/llm_client.py` pour exécution locale

### 3.3 Audio

- **sounddevice** : capture/lecture audio (`main.py:10`, `core/tts.py:17`)
- **Speech-to-Text** : `faster-whisper` ou `vosk` (`core/stt.py`)
- **Text-to-Speech** :
  - `edge-tts` (cloud Microsoft, gratuit)
  - `kokoro` (offline, ~330 Mo)
  - `elevenlabs` (cloud, clé API) (`core/tts.py`)

### 3.4 Vision & capture

- **mss** : capture d'écran (`actions/screen_processor.py`)
- **opencv-python** : webcam (`actions/screen_processor.py`)
- **Pillow** : traitement d'images (`actions/file_processor.py`, `ui.py`)

### 3.5 Contrôle du système & desktop

- **pyautogui** : clavier/souris (`actions/computer_control.py`, `actions/send_message.py`, etc.)
- **pyperclip** : copier/coller
- **pygetwindow** : gestion de fenêtres
- **psutil** : métriques système (`ui.py:14`)
- **pywinauto / pycaw / comtypes / win10toast** : spécifique Windows (conditions `win32`)

### 3.6 Web & navigateurs

- **Playwright** : contrôle automatique de navigateurs (`actions/browser_control.py`)
- **requests** : appels HTTP divers
- **beautifulsoup4** : parsing HTML
- **duckduckgo-search** : recherche web alternative

### 3.7 Dashboard web

- **FastAPI** + **uvicorn** (`dashboard/server.py`)
- **WebSocket** pour audio/commandes temps réel
- **cryptography** : chiffrement AES-256-CBC
- **qrcode[pil]** : génération de QR code pour l'appairage

### 3.8 Autres dépendances notables

- **youtube-transcript-api** : transcription YouTube
- **python-pptx** : présentations PowerPoint
- **send2trash** : suppression sécurisée

## 4. Composants principaux

### 4.1 `main.py` — Orchestrateur central

- Déclare les outils (functions) envoyés à Gemini (`TOOL_DECLARATIONS`)
- Gère la session `genai.Client.aio.live.connect`
- Exécute les appels d'outils dans `_execute_tool`
- Démarre le dashboard, la boucle audio, le relay téléphone

### 4.2 `ui.py` — Interface PyQt6

- Fenêtre principale, HUD animé, zone de drop de fichiers, log typewriter
- Overlay de configuration initiale (clé API, OS)
- Overlay de clé à distance / QR code
- Métriques système (CPU, RAM, GPU, température)

### 4.3 `dashboard/server.py` — Serveur web local

- FastAPI sur le port 8000 (HTTP) ou 8000/8001 (HTTPS avec certificats commités)
- Authentification par bearer token + PIN à 6 caractères à usage unique
- Upload de fichiers jusqu'à 500 Mo
- WebSocket audio depuis le téléphone
- Relai de commandes texte vers la boucle Gemini

### 4.4 `core/llm_client.py`

- Client Ollama / OpenAI-compatible avec streaming
- Démarrage automatique d'Ollama (`ollama serve`)
- Warmup du modèle avec KV-cache

### 4.5 `memory/memory_manager.py`

- Mémoire long terme structurée en JSON (`identity`, `preferences`, `projects`, `relationships`, `wishes`, `notes`)
- Limite de taille arbitraire (`MEMORY_MAX_CHARS = 2200`)
- Raccourcis `remember` / `forget`

### 4.6 `actions/*` — Moteurs d'actions

17 modules, chacun implémentant un domaine d'action. La signature est homogène :

```python
fonction(parameters: dict, response=None, player=None, session_memory=None) -> str
```

## 5. Flux de données global

```
Utilisateur (voix ou texte)
    ↓
PyQt6 UI / Microphone / Dashboard web
    ↓
main.py (JarvisLive)
    ↓
Google Gemini Live API (audio + tool calls)
    ↓
_actions/<module>.py (exécution sur le système local)
    ↓
Retour audio/texte à l'utilisateur + mémorisation JSON
```

## 6. Points de vigilance immédiate (cartographie)

- **Aucun Docker / CI-CD / tests** présent dans le dépôt.
- **Aucun fichier `.env`** ou gestion de secrets : la clé API est stockée en clair dans `config/api_keys.json`.
- **Certificats SSL privés commités** : `config/certs/jarvis.crt` et `config/certs/jarvis.key`.
- **Architecture monolithique** : `main.py` et `ui.py` dépassent respectivement 45 Ko et 68 Ko.
- **Dépendances partielles** : de nombreux paquets ne sont pas dans `requirements.txt` mais installés à la volée par `core/installer.py`.
