# Audit de performance — MARK XLVI

## 1. Méthodologie

Cet audit est basé sur l'analyse statique du code. Aucun profilage runtime n'a été effectué. Les conclusions reposent sur l'identification de patterns connus, de boucles, de requêtes réseau, d'appels système et d'allocations potentiellement coûteuses.

## 2. Goulets d'étranglement majeurs

### 2.1 Attente réseau et temps de réponse de Gemini

La boucle principale est entièrement tributaire du modèle Gemini Live (`models/gemini-2.5-flash-native-audio-preview-12-2025`). La latence de réponse et le streaming audio conditionnent l'expérience utilisateur. Le code ne peut pas optimiser cette latence, mais il peut la rendre pire par des appels synchrones bloquants.

### 2.2 Exécution synchrone des outils dans le thread de l'event loop

```@c:\Users\yoann\devin\Mark\Mark-XLVI\main.py:596-671
if name == "open_app":
    r = await loop.run_in_executor(None, lambda: open_app(parameters=args, ...))
...
elif name == "browser_control":
    r = await loop.run_in_executor(None, lambda: browser_control(parameters=args, ...))
```

Toutes les actions sont exécutées via `run_in_executor(None, ...)`. Bien que cela évite le blocage de l'event loop, le thread pool par défaut est limité (taille égale au nombre de CPU × 5). Un outil long (ex: recherche de vols, build de projet, génération de code) peut saturer les workers et retarder l'exécution des suivants.

### 2.3 Détection du modèle Ollama et warmup

```@c:\Users\yoann\devin\Mark\Mark-XLVI\core\llm_client.py:62-122
def ensure_ollama_running(timeout: int = 15) -> bool:
    ...
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(1.0)
        if _is_up():
            return True
```

Attente active de 1 seconde entre chaque vérification. Si Ollama est lent à démarrer, cette boucle consomme un thread bloqué pendant 15 secondes.

### 2.4 Chargement et warmup Kokoro

```@c:\Users\yoann\devin\Mark\Mark-XLVI\core\tts.py:214-309
class KokoroTTSEngine:
    def __init__(self, voice: str = "af_heart", speed: float = 1.0):
        ...
        self._init()   # blocking, but called from background thread
```

Le modèle Kokoro (~330 Mo) est chargé et compilé dans un thread d'arrière-plan. Cependant, le premier appel `speak()` est bloquant jusqu'à ce que le pipeline soit prêt. Aucun mécanisme de chargement paresseux ou de timeout n'est visible.

### 2.5 Capture d'écran / webcam

```@c:\Users\yoann\devin\Mark\Mark-XLVI\actions\screen_processor.py
```

La capture d'écran avec `mss` et la webcam avec `cv2` produisent des images de haute résolution. Elles sont encodées en base64 puis envoyées à Gemini. Aucun redimensionnement systématique n'est appliqué, ce qui augmente la taille du payload et la latence réseau.

## 3. Appels inutiles ou redondants

### 3.1 Relecture de `api_keys.json` à chaque appel

Chaque module `actions/` lit le fichier JSON de configuration pour récupérer la clé API. Exemples :

- `actions/web_search.py:16-18`
- `actions/desktop.py:26-29`
- `actions/code_helper.py:21-23`
- `actions/dev_agent.py:22-24`

Cela multiplie les accès disque et les opérations de parsing JSON. La clé devrait être passée une fois par le dispatcher.

### 3.2 Reconnexion en boucle infinie sans backoff exponentiel

```@c:\Users\yoann\devin\Mark\Mark-XLVI\main.py:939-952
except Exception as e:
    print(f"[JARVIS] Error: {e}")
    traceback.print_exc()
finally:
    self.session = None
...
print("[JARVIS] Reconnecting in 3s...")
await asyncio.sleep(3)
```

En cas d'erreur répétée (clé API invalide, réseau indisponible), le programme reconnecte toutes les 3 secondes indéfiniment. Cela consomme du CPU, de la mémoire et des ressources réseau sans fin.

### 3.3 `load_memory()` à chaque appel `save_memory`

```@c:\Users\yoann\devin\Mark\Mark-XLVI\memory\memory_manager.py:111-118
def update_memory(memory_update: dict) -> dict:
    memory = load_memory()
    if _recursive_update(memory, memory_update):
        save_memory(memory)
```

Chaque mise à jour de mémoire relit le fichier JSON complet. Cela est acceptable pour un petit fichier, mais devient un goulot si la mémoire grossit.

### 3.4 Métriques système : appels `subprocess` et commandes externes

```@c:\Users\yoann\devin\Mark\Mark-XLVI\ui.py:124-230
```

La collecte GPU/température lance `nvidia-smi`, `rocm-smi`, `intel_gpu_top`, `powermetrics`, `osx-cpu-temp`, ou PowerShell. Ces appels sont exécutés toutes les 1,5 secondes. Sur un système sans GPU, le code tente successivement plusieurs commandes non disponibles, ce qui est coûteux en termes de lancement de processus.

## 4. Traitements coûteux

### 4.1 Génération de code multi-fichiers (`dev_agent.py`)

`dev_agent.py` appelle Gemini pour chaque fichier d'un projet, puis installe les dépendances et exécute le projet. C'est un processus potentiellement long (plusieurs requêtes LLM + `pip install` + `subprocess.run`).

### 4.2 Traitement de fichiers uploadés (`file_processor.py`)

`file_processor.py` traite des images, PDF, vidéos, audio, CSV, etc. Les conversions vidéo/audio et OCR sont intensives. Le code ne semble pas limiter la taille des fichiers traités ni utiliser de file d'attente.

### 4.3 Recherche web et comparaison

```@c:\Users\yoann\devin\Mark\Mark-XLVI\actions\web_search.py:71-95
def _compare(items: list[str], aspect: str) -> str:
    all_results: dict[str, list] = {}
    for item in items:
        try:
            all_results[item] = _ddg_search(f"{item} {aspect}", max_results=3)
```

La comparaison effectue N requêtes DuckDuckGo séquentielles (pas de parallélisme). Si `items` est grand, la latence est linéaire.

### 4.4 Traitement des résultats YouTube par regex sur du HTML brut

```@c:\Users\yoann\devin\Mark\Mark-XLVI\actions\youtube_video.py:88-91
r    = requests.get(search_url, headers=HEADERS, timeout=10)
html = r.text
video_ids = re.findall(r'"videoId":"([A-Za-z0-9_-]{11})"', html)
```

Parsing HTML de pages YouTube entières par regex, potentiellement très gourmand en mémoire.

## 5. Optimisations recommandées

### 5.1 Caching de la configuration et des clients API

- Charger `api_keys.json` une seule fois au démarrage et stocker la clé dans l'instance `JarvisLive`.
- Réutiliser un seul `genai.Client` ou le partager via un singleton, plutôt que d'en recréer un à chaque appel d'action.

### 5.2 Backoff exponentiel et circuit breaker

Remplacer la reconnexion fixe de 3s par un backoff exponentiel (3s, 6s, 12s, 30s, max 5 minutes) et un compteur d'erreurs. En cas d'erreur critique (clé invalide), arrêter et informer l'utilisateur.

### 5.3 Pool de workers dédié pour les actions longues

Créer un `ThreadPoolExecutor` avec un nombre de workers adapté (par exemple 5) et utiliser des timeouts stricts. Les actions longues (build, flight, video) devraient être marquées et potentiellement exécutées en arrière-plan sans bloquer la session principale.

### 5.4 Redimensionnement systématique des captures

Avant d'envoyer une image à Gemini, la redimensionner à une résolution maximale (ex: 1024×1024) et la compresser en JPEG avec qualité 80. Cela réduit la latence réseau et le coût API.

### 5.5 Lazy loading et cache des moteurs TTS/STT

Ne pas charger Kokoro/Whisper au démarrage si l'utilisateur a choisi EdgeTTS/Vosk. Utiliser un cache d'engine pour éviter les rechargements.

### 5.6 Métriques système : polling adaptatif

- Période de 1,5 s est correcte, mais éviter les appels multiples si aucune carte GPU n'est détectée.
- Mémoriser l'absence de commandes (`nvidia-smi`, `rocm-smi`, etc.) et ne pas les retenter à chaque cycle.

### 5.7 Parallélisme des requêtes web

Utiliser `asyncio.gather` ou `asyncio.TaskGroup` pour exécuter les recherches `DuckDuckGo` en parallèle dans `_compare()`.

### 5.8 Parsing JSON structuré pour YouTube

Utiliser l'API YouTube Data (si clé dispo) ou `yt-dlp` pour extraire les métadonnées, plutôt que du parsing regex de HTML.

## 6. Consommation mémoire

### 6.1 Historique WebSocket non limité en mémoire

```@c:\Users\yoann\devin\Mark\Mark-XLVI\dashboard\server.py:437-440
async def broadcast(self, msg: dict) -> None:
    self._history.append(msg)
    if len(self._history) > 300:
        self._history = self._history[-300:]
```

La limite de 300 messages est correcte, mais chaque message peut être gros (upload de 500 Mo, images base64). Le stockage en mémoire des fichiers est limité, mais les métadonnées peuvent être importantes.

### 6.2 Files audio

```@c:\Users\yoann\devin\Mark\Mark-XLVI\main.py:921-922
self.audio_in_queue   = asyncio.Queue()
self.out_queue        = asyncio.Queue(maxsize=200)
```

`audio_in_queue` est illimitée. Si la lecture audio est plus lente que la réception, la mémoire peut croître rapidement.

### 6.3 Mémoire long terme

`MEMORY_MAX_CHARS = 2200` est une limite arbitraire et faible. Elle force la troncature silencieuse sans stratégie de priorisation. Les informations importantes peuvent être perdues.

## 7. Synthèse des performances

| Domaine | État | Recommandation | Effort |
|---|---|---|---|
| Exécution des outils | Goulot potentiel | Thread pool dédié + timeouts | Moyen |
| Reconnexion Gemini | Boucle infinie fixe | Backoff exponentiel + circuit breaker | Faible |
| Lecture config | Redondante | Cacher au démarrage | Faible |
| Capture d'écran | Payloads lourds | Redimensionner/compresser avant envoi | Moyen |
| Métriques système | Appels processus répétés | Mémoriser l'absence de commandes | Faible |
| Recherche comparaison | Requêtes séquentielles | Paralléliser avec `asyncio.gather` | Faible |
| Parsing YouTube | Regex sur HTML | Utiliser API/yt-dlp | Moyen |
| TTS Kokoro | Chargement lourd | Lazy loading + cache | Moyen |
| Files audio | Queue illimitée | Limiter la taille + backpressure | Faible |
| Mémoire long terme | Troncature silencieuse | Base vectorielle ou base de données légère | Important |

## 8. Citations clés

- Exécution synchrone outils : `main.py:596-671`
- Reconnexion en boucle : `main.py:939-952`
- Lecture config répétée : `actions/web_search.py:16-18`, `actions/desktop.py:26-29`, `actions/code_helper.py:21-23`, `actions/dev_agent.py:22-24`
- Attente Ollama : `core/llm_client.py:62-122`
- Kokoro init : `core/tts.py:214-309`
- Métriques système : `ui.py:124-230`
- Recherche web séquentielle : `actions/web_search.py:71-95`
- YouTube regex : `actions/youtube_video.py:88-91`
- Historique dashboard : `dashboard/server.py:437-440`
- Files audio : `main.py:921-922`
