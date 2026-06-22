# Dette technique — MARK XLVI

## Légende

- **Critique** : risque de sécurité, perte de données, ou blocage total.
- **Élevée** : impact significatif sur la maintenabilité, la fiabilité ou la performance.
- **Moyenne** : gêne récurrente, contournable, mais coûteuse à long terme.
- **Faible** : polish, style, ou amélioration mineure.

---

## Dette critique

| # | Problème | Fichier(s) | Justification |
|---|---|---|---|
| 1 | **Clé privée SSL commitée en clair** | `config/certs/jarvis.key`, `config/certs/jarvis.crt` | La clé privée est publique. N'importe qui peut usurper le serveur HTTPS ou déchiffrer le trafic. Voir `dashboard/server.py:759-764`. |
| 2 | **Exécution de code généré par LLM** | `actions/desktop.py:83-101` | `exec(compile(code, ...))` dans un sandbox insuffisant. RCE potentiel via commande vocale. |
| 3 | **Injection de commandes via `shell=True`** | `actions/open_app.py:83-99`, `dashboard/server.py:185-186`, `actions/computer_settings.py:124-157`, `actions/dev_agent.py:279-285` | Des entrées utilisateur ou des chemins variables sont passés à `subprocess.Popen/run(..., shell=True)`. |
| 4 | **Clé API stockée en clair** | `memory/config_manager.py:20-35`, `main.py:52-54` | Aucun chiffrement, aucune variable d'environnement. Fuite immédiate si le dossier est copié ou commité. |
| 5 | **Modification automatique du firewall** | `dashboard/server.py:99-232` | Le programme demande l'élévation et expose le port 8000/8001 sur 0.0.0.0 avec un serveur aux droits élevés. |

---

## Dette élevée

| # | Problème | Fichier(s) | Justification |
|---|---|---|---|
| 6 | **Fichiers monolithiques surchargés** | `main.py` (969 lignes), `ui.py` (1800 lignes), `dashboard/server.py` (795 lignes), `actions/browser_control.py` (893 lignes) | Responsabilités multiples, difficulté de relecture et de test. |
| 7 | **Authentification dashboard faible** | `dashboard/server.py:391-396` | PIN de 6 caractères, sans rate limiting, sans PBKDF2, dérivation SHA-256 avec sel hardcodé. |
| 8 | **Chiffrement maison sans intégrité** | `dashboard/server.py:72-90` | AES-256-CBC sans MAC, sel constant, dérivation directe d'un PIN court. Vulnérable au padding oracle / bit-flipping. |
| 9 | **Upload/serve de fichiers sans contrôle** | `dashboard/server.py:642-721` | Aucune vérification de type, taille, ou contenu. Token passé en query param. Path traversal partiel. |
| 10 | **Reconnexion en boucle infinie fixe** | `main.py:939-952` | En cas d'erreur persistante (clé invalide, réseau), le programme boucle toutes les 3 secondes sans backoff. |
| 11 | **Dépendances non versionnées** | `requirements.txt:1-28` | Aucune version ni hash. Risque de rupture et d'installation de versions vulnérables. |
| 12 | **Deux SDK Gemini installés** | `requirements.txt:2-3`, `main.py:11-12` | `google-genai` et `google-generativeai` listés ; seul le premier est utilisé. Conflit potentiel. |
| 13 | **Couplage fort UI ↔ logique métier** | `main.py:474-484`, `main.py:596-697` | L'orchestrateur appelle directement `self.ui.set_state`, `self.ui.write_log`. L'UI est requise pour tester. |
| 14 | **Actions reçoivent l'objet UI comme `player`** | `actions/web_search.py:116`, `actions/desktop.py:434`, `actions/computer_control.py` | Les modules d'action produisent des effets de bord visuels. Pas d'interface abstraite. |
| 15 | **Mémoire long terme tronquée silencieusement** | `memory/memory_manager.py:58-68` | `MEMORY_MAX_CHARS = 2200` puis suppression des entrées les plus anciennes. Perte d'information sans avertissement. |
| 16 | **Configuration et données dans le répertoire du projet** | `memory/config_manager.py:10-12`, `memory/memory_manager.py:14-15` | `api_keys.json` et `long_term.json` sont stockés à côté du code source. Problème de packaging et de permissions. |
| 17 | **Auto-installation de paquets Python** | `core/installer.py:68-82`, `core/tts.py:170-175` | `pip install` exécuté automatiquement. Risque d'installation de paquets malveillants ou de conflits de versions. |
| 18 | **Capture d'écran/webcam sans indicateur** | `actions/screen_processor.py` | Envoi d'images/vidéo vers Gemini sans consentement explicite visuel. |
| 19 | **Parsing HTML par regex (YouTube)** | `actions/youtube_video.py:88-91` | `re.findall(r'"videoId":"([A-Za-z0-9_-]{11})"', html)` est fragile et potentiellement coûteux. |

---

## Dette moyenne

| # | Problème | Fichier(s) | Justification |
|---|---|---|---|
| 20 | **Duplication de `get_base_dir()`** | `main.py:37-40`, `core/llm_client.py:33-36`, `memory/config_manager.py:5-8`, `memory/memory_manager.py:8-11`, `actions/desktop.py:21-24`, `actions/computer_control.py:27-30`, `actions/code_helper.py:9-12`, `actions/dev_agent.py:9-12`, `actions/web_search.py:6-9`, `actions/send_message.py:21-24`, `ui.py:31-34` | Au moins 11 implémentations quasi identiques. |
| 21 | **Duplication de la lecture de `api_keys.json`** | `actions/web_search.py:16-18`, `actions/desktop.py:26-29`, `actions/code_helper.py:21-23`, `actions/dev_agent.py:22-24`, `dashboard/server.py:61-67` | Chaque module relit le fichier. Devrait être injecté. |
| 22 | **Dépendances optionnelles non listées** | `requirements.txt`, `actions/file_processor.py`, `core/tts.py`, `core/stt.py` | `pandas`, `openpyxl`, `python-docx`, `pydub`, `faster-whisper`, `vosk`, `edge-tts`, `kokoro`, `soundfile`, `miniaudio` sont absents de `requirements.txt`. |
| 23 | **Client Ollama inutilisé par `main.py`** | `core/llm_client.py:1-587` | Deux clients LLM coexistent sans abstraction. Code mort ou confusant. |
| 24 | **Historique WebSocket en mémoire non chiffré** | `dashboard/server.py:373-377` | `_history` conserve les 300 derniers messages. Aucune persistance sécurisée ni rotation. |
| 25 | **File audio illimitée** | `main.py:921` | `audio_in_queue` est une `asyncio.Queue()` sans maxsize. Risque de croissance mémoire si le playback est lent. |
| 26 | **Métriques système : appels processus répétés** | `ui.py:124-230` | `nvidia-smi`, `rocm-smi`, `intel_gpu_top`, etc. sont relancés à chaque cycle même si absents. |
| 27 | **Requêtes de comparaison web séquentielles** | `actions/web_search.py:71-95` | `_compare()` boucle sur les items sans parallélisme. Latence linéaire. |
| 28 | **Attente active Ollama** | `core/llm_client.py:114-119` | `time.sleep(1.0)` en boucle. Un thread bloqué pendant le timeout. |
| 29 | **Pas de gestion des erreurs réseau structurées** | `actions/web_search.py:120-141`, `actions/youtube_video.py` | Retries manquants, fallbacks bruts. |
| 30 | **Commentaires et messages mélangés anglais/turc** | `actions/dev_agent.py:327`, `actions/desktop.py` | Mélange de langues dans les docstrings et commentaires (`Varsa`, `Güvenli dizin`). Réduit la cohérence. |
| 31 | **Gestion des types et des entrées partielle** | `actions/open_app.py`, `actions/computer_settings.py` | Paramètres castés sans validation stricte. |
| 32 | **Pas de tests** | Tout le dépôt | Aucun répertoire `tests/`, aucune CI, aucune vérification automatisée. |

---

## Dette faible

| # | Problème | Fichier(s) | Justification |
|---|---|---|---|
| 33 | **Style de code inconsistent** | Divers | Imports groupés de manière variable, longueur de lignes, utilisation de `_` pour les noms de fonctions. |
| 34 | **Messages d'erreur verbaux imprimés** | `main.py`, `actions/*.py` | Beaucoup de `print()` au lieu d'un logger structuré. |
| 35 | **Nom du projet dans le setup incorrect** | `setup.py:10` | Référence à "MARK XXV" alors que le projet est "MARK XLVI". |
| 36 | **README manque de détails techniques** | `readme.md` | Pas de documentation architecturelle, pas de sécurité, pas de configuration avancée. |
| 37 | **Constantes magiques** | `main.py:46-50`, `dashboard/server.py:40-41` | Échantillonnage audio, tailles de queue, limites upload codées en dur. |
| 38 | **Absence de packaging moderne** | `setup.py` | Utilise `setup.py` avec subprocess au lieu de `pyproject.toml`. |
| 39 | **Fichiers vides** | `dashboard/__init__.py` | Fichier vide sans utilité apparente. |
| 40 | **Utilisation de `os._exit` brutal** | `main.py:676-680` | `shutdown_jarvis` appelle `os._exit(0)` sans nettoyer les ressources. |

---

## Répartition par criticité

| Criticité | Nombre |
|---|---|
| Critique | 5 |
| Élevée | 14 |
| Moyenne | 13 |
| Faible | 8 |
| **Total** | **40** |

---

## Citations clés

- Clé privée : `config/certs/jarvis.key:1-28`
- RCE : `actions/desktop.py:83-101`
- Shell injection : `actions/open_app.py:83-99`
- Clé API clair : `memory/config_manager.py:20-35`
- Firewall auto : `dashboard/server.py:99-232`
- Monolithes : `main.py:1-969`, `ui.py:1-1800`, `dashboard/server.py:1-795`
- Auth faible : `dashboard/server.py:391-396`, `dashboard/server.py:72-90`
- Upload non contrôlé : `dashboard/server.py:642-721`
- Reconnexion infinie : `main.py:939-952`
- Dépendances non versionnées : `requirements.txt:1-28`
- Couplage UI : `main.py:596-697`
- Mémoire tronquée : `memory/memory_manager.py:58-68`
