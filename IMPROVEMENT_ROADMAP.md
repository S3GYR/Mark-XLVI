# Roadmap d'amélioration — MARK XLVI

> Cette roadmap classe les actions par priorité et estime l'effort (Faible / Moyen / Important). Elle est basée sur les conclusions des audits `SECURITY_AUDIT.md`, `ARCHITECTURE_REVIEW.md`, `PERFORMANCE_AUDIT.md` et `TECHNICAL_DEBT.md`.

---

## Phase 1 — Sécurité critique (P0)

**Objectif** : supprimer les risques de sécurité bloquants avant toute utilisation réelle.

| # | Action | Fichier(s) concernés | Justification | Effort |
|---|---|---|---|---|
| 1.1 | **Révoquer et supprimer la clé privée `jarvis.key` du dépôt** | `config/certs/jarvis.key`, `config/certs/jarvis.crt` | Clé privée publique = compromission totale du TLS. | Faible |
| 1.2 | **Générer des certificats auto-signés à la volée** | `dashboard/server.py` | Utiliser `cryptography` pour créer un certificat unique par installation. | Moyen |
| 1.3 | **Supprimer l'exécution de code généré par LLM** | `actions/desktop.py:83-101` | Remplacer `exec(compile(...))` par une API de haut niveau (pyautogui, pathlib) avec allow-list explicite. | Important |
| 1.4 | **Supprimer tous les `shell=True` sur des entrées utilisateur** | `actions/open_app.py`, `actions/computer_settings.py`, `actions/dev_agent.py`, `dashboard/server.py` | Utiliser des listes d'arguments et valider/sanitizer les entrées. | Moyen |
| 1.5 | **Chiffrer `api_keys.json` avec le trousseau OS** | `memory/config_manager.py` | Utiliser `keyring` ou DPAPI/macOS Keychain/Linux Secret Service. | Moyen |
| 1.6 | **Ne plus exposer le dashboard sur `0.0.0.0` par défaut** | `dashboard/server.py:786-793` | Lier par défaut à `127.0.0.1` et rendre l'accès LAN optionnel avec avertissement. | Faible |
| 1.7 | **Ajouter un rate limiting / tentative max sur le PIN** | `dashboard/server.py:481-500` | Bloquer après N échecs et forcer un nouveau QR code. | Moyen |

---

## Phase 2 — Refonte de l'architecture (P1)

**Objectif** : améliorer la maintenabilité, la testabilité et la scalabilité.

| # | Action | Fichier(s) concernés | Justification | Effort |
|---|---|---|---|---|
| 2.1 | **Extraire la configuration dans un module unique** | `memory/config_manager.py`, `config/__init__.py`, tous les `actions/*.py` | Éliminer les 11+ implémentations de `get_base_dir` et la lecture répétée de `api_keys.json`. | Moyen |
| 2.2 | **Créer une abstraction LLM unique** | `core/llm_client.py`, `main.py` | Fusionner le client Gemini de `main.py` et le client Ollama d'`llm_client.py` derrière une interface commune. | Moyen |
| 2.3 | **Découper `main.py` en modules** | `main.py` | Créer `jarvis/core/orchestrator.py`, `jarvis/core/tool_dispatcher.py`, `jarvis/audio/`. | Important |
| 2.4 | **Découper `ui.py` en widgets réutilisables** | `ui.py` | Séparer `HudCanvas`, `LogWidget`, `FileDropZone`, `SetupOverlay`, `RemoteKeyOverlay`. | Moyen |
| 2.5 | **Découper `dashboard/server.py` en routes** | `dashboard/server.py` | Routes dans `dashboard/routes/`, auth dans `dashboard/auth.py`, firewall dans `dashboard/network.py`. | Moyen |
| 2.6 | **Définir un protocole `LogSink`/`Player`** | `main.py`, `actions/*.py` | Permettre de brancher UI, fichier, ou stub de test. | Moyen |
| 2.7 | **Déplacer les données utilisateur hors du répertoire source** | `memory/config_manager.py`, `memory/memory_manager.py` | Utiliser `platformdirs` pour config et data. | Faible |
| 2.8 | **Migrer vers `pyproject.toml` et packaging moderne** | `setup.py`, `requirements.txt` | Remplacer le `setup.py` obsolète et les dépendances non versionnées. | Moyen |

---

## Phase 3 — Fiabilité et robustesse (P1/P2)

**Objectif** : réduire les erreurs silencieuses, les boucles infinies et les comportements fragiles.

| # | Action | Fichier(s) concernés | Justification | Effort |
|---|---|---|---|---|
| 3.1 | **Implémenter un backoff exponentiel et un circuit breaker** | `main.py:939-952` | Éviter la reconnexion toutes les 3 secondes en cas d'erreur répétée. | Faible |
| 3.2 | **Versionner figer les dépendances** | `requirements.txt` | Générer un `requirements.lock` et utiliser des groupes optionnels. | Faible |
| 3.3 | **Lister toutes les dépendances optionnelles** | `requirements.txt`, `core/installer.py`, `actions/file_processor.py` | Ajouter `[tts]`, `[stt]`, `[vision]`, `[dashboard]`, `[extras]`. | Moyen |
| 3.4 | **Supprimer `google-generativeai` si inutile** | `requirements.txt:3` | Éviter le conflit avec `google-genai`. | Faible |
| 3.5 | **Limiter la taille de `audio_in_queue`** | `main.py:921` | Ajouter `maxsize` et une politique de backpressure. | Faible |
| 3.6 | **Rendre la mémoire long terme robuste** | `memory/memory_manager.py` | Utiliser SQLite, Chroma ou une base vectorielle légère au lieu de JSON tronqué. | Important |
| 3.7 | **Ajouter une gestion d'erreurs structurée** | `actions/*.py`, `main.py` | Logger avec `logging` au lieu de `print`, avec niveaux et contexte. | Moyen |
| 3.8 | **Remplacer `os._exit` par un arrêt propre** | `main.py:676-680` | Nettoyer les ressources, fermer les WebSockets, arrêter les streams. | Faible |

---

## Phase 4 — Sécurité et dashboard (P2)

**Objectif** : durcir le dashboard et l'authentification.

| # | Action | Fichier(s) concernés | Justification | Effort |
|---|---|---|---|---|
| 4.1 | **Remplacer le chiffrement AES-CBC maison par un mécanisme standard** | `dashboard/server.py:72-90` | Utiliser HTTPS/TLS natif ou, si nécessaire, ChaCha20-Poly1305 avec PBKDF2 + sel aléatoire. | Moyen |
| 4.2 | **Valider et restreindre les uploads** | `dashboard/server.py:642-721` | Vérifier extension, MIME, taille, scanner basique, répertoire isolé. | Moyen |
| 4.3 | **Ne plus passer le token en query param** | `dashboard/server.py:711-721` | Utiliser des cookies sécurisés SameSite ou des liens temporaires signés. | Moyen |
| 4.4 | **Désactiver l'ouverture automatique du firewall** | `dashboard/server.py:99-232` | Transformer en action manuelle documentée avec avertissement. | Faible |
| 4.5 | **Indicateur visuel de capture écran/webcam** | `actions/screen_processor.py` | Montrer à l'utilisateur quand une image est capturée et envoyée. | Faible |
| 4.6 | **Restreindre les actions sensibles au réseau local** | `dashboard/server.py` | Refuser les commandes `computer_control`, `file_controller`, etc. depuis l'extérieur. | Moyen |

---

## Phase 5 — Performance et expérience utilisateur (P2)

**Objectif** : réduire la latence et la consommation de ressources.

| # | Action | Fichier(s) concernés | Justification | Effort |
|---|---|---|---|---|
| 5.1 | **Redimensionner et compresser les captures avant envoi** | `actions/screen_processor.py` | Réduire la taille des payloads Gemini. | Moyen |
| 5.2 | **Paralléliser les requêtes de comparaison web** | `actions/web_search.py:71-95` | Utiliser `asyncio.gather` pour les recherches DuckDuckGo. | Faible |
| 5.3 | **Mémoriser l'absence de commandes GPU** | `ui.py:124-230` | Éviter de relancer `nvidia-smi`, `rocm-smi`, etc. à chaque cycle. | Faible |
| 5.4 | **Lazy loading des moteurs TTS/STT** | `core/tts.py`, `core/stt.py` | Ne charger Kokoro/Whisper que si l'utilisateur les choisit. | Moyen |
| 5.5 | **Utiliser un pool de threads dédié pour les actions longues** | `main.py:596-671` | Éviter de bloquer le thread pool par défaut. | Moyen |
| 5.6 | **Remplacer le parsing YouTube par regex** | `actions/youtube_video.py` | Utiliser `yt-dlp` ou l'API YouTube Data. | Moyen |
| 5.7 | **Ajouter des timeouts stricts sur les actions** | `main.py`, `actions/*.py` | Interrompre les opérations bloquantes au-delà d'une limite. | Moyen |

---

## Phase 6 — Tests, qualité et documentation (P3)

**Objectif** : industrialiser le projet.

| # | Action | Fichier(s) concernés | Justification | Effort |
|---|---|---|---|---|
| 6.1 | **Créer une suite de tests unitaires** | `tests/` | Mocker les actions, les clients API, les subprocess. | Important |
| 6.2 | **Ajouter des tests d'intégration audio** | `tests/audio/` | Vérifier les flux audio sans réseau. | Moyen |
| 6.3 | **Mettre en place une CI/CD** | `.github/workflows/` | Lint, tests, audit de dépendances. | Moyen |
| 6.4 | **Ajouter un audit de dépendances** | `requirements.txt` | Intégrer `pip-audit` ou `safety`. | Faible |
| 6.5 | **Documenter l'architecture et la sécurité** | `docs/`, `README.md` | Ajouter un guide d'installation sécurisée et un ADR. | Moyen |
| 6.6 | **Corriger le message `MARK XXV` dans setup.py** | `setup.py:10` | Cohérence du nom de projet. | Faible |
| 6.7 | **Uniformiser la langue des commentaires** | `actions/dev_agent.py`, `actions/desktop.py` | Traduire/supprimer les commentaires turcs. | Faible |
| 6.8 | **Ajouter Docker (optionnel)** | `Dockerfile`, `docker-compose.yml` | Faciliter le déploiement et l'isolation. | Moyen |

---

## Planning proposé

| Phase | Durée estimée | Livrable clé |
|---|---|---|
| P0 — Sécurité critique | 1-2 semaines | Clés/certificats générés à la volée, RCE supprimé, `shell=True` éliminé, API key chiffrée |
| P1 — Architecture | 3-4 semaines | `pyproject.toml`, modules extraits, abstraction LLM, protocole `LogSink` |
| P1/P2 — Fiabilité | 2-3 semaines | Backoff, dépendances versionnées, mémoire SQLite, logging structuré |
| P2 — Dashboard sécurisé | 2 semaines | Auth robuste, upload contrôlé, TLS propre, firewall manuel |
| P2 — Performance | 2-3 semaines | Compression images, pool threads, lazy loading, parsing YouTube propre |
| P3 — Tests & qualité | 2-3 semaines | Tests unitaires, CI, audit dépendances, documentation |

**Total estimé** : **12 à 17 semaines** pour une version industrialisée et sécurisée.

---

## Matrice priorité / effort

| Priorité | Faible | Moyen | Important |
|---|---|---|---|
| **P0 Critique** | Lier dashboard à 127.0.0.1 par défaut | Chiffrer API key, rate limiting PIN, générer certificats | Supprimer RCE, supprimer `shell=True`, supprimer clé privée commitée |
| **P1 Élevée** | Déplacer données utilisateur, versionner dépendances | Refonte modules, abstraction LLM, LogSink, pyproject.toml | Découper `main.py`, `ui.py`, `dashboard/server.py` |
| **P2 Moyenne** | Backoff exponentiel, firewall manuel, indicateur capture | Upload sécurisé, chiffrement standard, timeouts | Mémoire SQLite, tests unitaires, CI/CD |
| **P3 Faible** | Corrections mineures (nom, langue) | Docker, documentation | — |

---

## Citations clés

- Clé privée commitée : `config/certs/jarvis.key:1-28`
- RCE desktop : `actions/desktop.py:83-101`
- Shell injection : `actions/open_app.py:83-99`
- API key clair : `memory/config_manager.py:20-35`
- Firewall auto : `dashboard/server.py:99-232`
- Auth PIN faible : `dashboard/server.py:391-396`
- Chiffrement maison : `dashboard/server.py:72-90`
- Monolithes : `main.py:1-969`, `ui.py:1-1800`, `dashboard/server.py:1-795`
- Reconnexion infinie : `main.py:939-952`
- Mémoire tronquée : `memory/memory_manager.py:58-68`
- Dépendances non versionnées : `requirements.txt:1-28`
