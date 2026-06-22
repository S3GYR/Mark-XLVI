# Audit de sécurité — MARK XLVI

> ⚠️ Ce rapport identifie des **vulnérabilités critiques**. Toute mise en production avant correction est fortement déconseillée.

## 1. Secrets exposés

### 1.1 Clé privée SSL commitée — CRITIQUE

Le dépôt contient une paire de certificats auto-signés utilisée par le serveur HTTPS du dashboard :

```
config/certs/jarvis.crt
config/certs/jarvis.key
```

La clé privée RSA est **commitée en clair** dans le dépôt public :

```@c:\Users\yoann\devin\Mark\Mark-XLVI\config\certs\jarvis.key:1-28
-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA2Dey8TWaENR3GGfJH9cr8qdE0tMzZOTD/9QdA5O9FI68U44s
...
-----END RSA PRIVATE KEY-----
```

**Impact** : n'importe qui peut déchiffrer le trafic TLS, usurper le serveur, ou faire du "man-in-the-middle" sur le port 8000/8001. Le certificat est également réutilisé par tous les utilisateurs du projet.

**Utilisation** : `dashboard/server.py:759-764`, `dashboard/server.py:780-788`

### 1.2 Clé API Gemini stockée en clair

La clé API Gemini est écrite dans `config/api_keys.json` sans chiffrement :

```@c:\Users\yoann\devin\Mark\Mark-XLVI\memory\config_manager.py:20-35
def save_api_keys(gemini_api_key: str) -> None:
    ...
    data["gemini_api_key"] = gemini_api_key.strip()
    CONFIG_FILE.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8"
    )
```

Lecture directe sans chiffrement : `main.py:52-54`, `actions/web_search.py:16-18`, `actions/desktop.py:26-29`, `actions/code_helper.py:21-23`, `actions/dev_agent.py:22-24`.

### 1.3 Pas de fichier `.env` ou gestion centralisée de secrets

Aucun `.env.example`, `.env`, ou variable d'environnement n'est utilisée. Les secrets sont stockés dans des fichiers JSON dans le répertoire du projet.

## 2. Exécution de code arbitraire (RCE)

### 2.1 `exec(compile(...))` sur code généré par LLM — CRITIQUE

`actions/desktop.py` génère du code Python avec Gemini, puis l'exécute dans un "bac à sable" minimal :

```@c:\Users\yoann\devin\Mark\Mark-XLVI\actions\desktop.py:83-101
def _execute_generated_code(code: str, player=None) -> str:
    ...
    sandbox      = _build_sandbox()
    ...
    exec(compile(code, "<jarvis_desktop>", "exec"), sandbox)
    return "\n".join(output_lines) if output_lines else "Done."
```

Le sandbox fournit `pyautogui`, `Path`, `shutil.copy2/copytree/disk_usage`, `os.path`, `time`, `ctypes`, `winreg`.

**Problèmes** :

- Le sandbox n'est **pas sûr** : `Path` permet de lire n'importe quel fichier, `pyautogui` peut prendre le contrôle total du clavier/souris, `ctypes` permet d'appeler des fonctions Windows natives, `winreg` lit le registre.
- Le LLM peut être "jailbreaké" pour générer du code malveillant malgré les instructions du prompt (`actions/desktop.py:132-138`).
- Aucune vérification syntaxique, aucune limitation de ressources (CPU/mémoire), aucun timeout.

**Impact** : exécution de code arbitraire sur le poste de l'utilisateur, potentiellement avec les droits du processus Python.

### 2.2 `subprocess` avec `shell=True` — ÉLEVÉ

Plusieurs appels shell sont dangereux car ils interprètent des chaînes construites à partir d'entrées utilisateur ou de variables système :

```@c:\Users\yoann\devin\Mark\Mark-XLVI\actions\open_app.py:83-99
try:
    subprocess.Popen(
        app_name,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
...
if ":" in app_name:
    try:
        subprocess.Popen(f"start {app_name}", shell=True)
```

`app_name` est passé par l'utilisateur via l'outil `open_app`. `shell=True` permet l'injection de commandes (ex: `app_name = "notepad & calc"` ou `app_name = "cmd /c del C:\\"`).

Autres `shell=True` identifiés :

- `dashboard/server.py:185-186` : exécution d'un fichier `.bat` généré pour modifier le firewall. Le fichier est écrit avec `os.write(fd, bat_body.encode("mbcs"))`.
- `actions/computer_settings.py:124-128` et `:153-157` : ajustement de la luminosité avec `xrandr` via une commande Python inline complexe.
- `actions/dev_agent.py:279-285` : ouverture de VSCode avec `shell=True`.

### 2.3 Installation automatique de paquets Python — ÉLEVÉ

`core/installer.py` exécute `pip install` automatiquement si un module manque :

```@c:\Users\yoann\devin\Mark\Mark-XLVI\core\installer.py:68-82
def _pip(package: str, log: Callable | None = None) -> bool:
    result = subprocess.run(
        [
            sys.executable, "-m", "pip", "install", package,
            "--quiet", "--disable-pip-version-check",
        ],
        capture_output=True,
    )
```

```@c:\Users\yoann\devin\Mark\Mark-XLVI\core\tts.py:170-175
result = subprocess.run(
    [sys.executable, "-m", "pip", "install", "kokoro>=0.9",
     "--upgrade", "--quiet", "--disable-pip-version-check"],
    capture_output=True,
)
```

**Impact** : installation non contrôlée depuis PyPI. Un paquet malicieux peut être pullé, surtout si le LLM demande un nom de paquet arbitraire.

### 2.4 Exécution de scripts téléchargés

`actions/code_helper.py` écrit et exécute des fichiers générés par le LLM sur le Desktop (`_resolve_save_path`), puis les lance avec `subprocess.run` sans sandbox : `actions/code_helper.py:196-216`.

`actions/dev_agent.py` génère des projets entiers et les exécute : `_run_file`/`_install_dependencies`.

## 3. Risques liés au dashboard web

### 3.1 Authentification par PIN à 6 caractères — ÉLEVÉ

```@c:\Users\yoann\devin\Mark\Mark-XLVI\dashboard\server.py:391-396
def new_key(self, expiry_secs: int = 600) -> str:
    ...
    key = ''.join(secrets.choice(_KEY_CHARS) for _ in range(6))
```

Espace de clés : 31 caractères ^ 6 ≈ 887 millions de combinaisons. Sans limitation de débit, c'est brute-forçable en quelques minutes/heures.

### 3.2 Token d'accès passé en query param pour les téléchargements

```@c:\Users\yoann\devin\Mark\Mark-XLVI\dashboard\server.py:711-721
@app.get("/uploads/{filename}")
async def download_file(filename: str, token: str = ""):
    tok = token.strip()
    if not tok or tok not in self._tokens:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
```

Le token apparaît dans les logs du serveur, l'historique du navigateur, et peut être capturé. Le `filename` n'est pas vérifié en dehors d'une simple regex `[/\\]` : vulnérabilité de type path traversal potentielle (ex: `filename="..\\.ssh\\id_rsa"` sur Linux si les uploads sont dans le home).

### 3.3 Upload sans vérification de type de fichier — ÉLEVÉ

```@c:\Users\yoann\devin\Mark\Mark-XLVI\dashboard\server.py:642-686
@app.post("/api/upload")
async def upload_file(req: Request, file: UploadFile = FastAPIFile(...)):
    ...
    safe = _safe_filename(file.filename or "upload")
    dest = self._uploads_dir / safe
```

Aucune vérification du type MIME, de l'extension, ni d'analyse antivirus. Le répertoire d'upload est ensuite servi via `/uploads/{filename}`. Un fichier `.exe` ou `.html` malveillant peut être uploadé et exécuté côté client par un autre utilisateur du réseau local.

### 3.4 Chiffrement AES personnalisé

```@c:\Users\yoann\devin\Mark\Mark-XLVI\dashboard\server.py:72-90
_AES_SALT = b'JARVIS-DASHBOARD-v1'

def _derive_key(session_key: str) -> bytes:
    return hashlib.sha256(session_key.encode('utf-8') + _AES_SALT).digest()

def _decrypt_cbc(aes_key: bytes, enc_b64: str) -> str:
    raw      = base64.b64decode(enc_b64)
    iv, ct   = raw[:16], raw[16:]
    dec      = Cipher(algorithms.AES(aes_key), modes.CBC(iv)).decryptor()
```

- Pas de PBKDF2, pas de itérations : dérivation SHA-256 d'un PIN de 6 caractères.
- Le sel est **hardcodé** et identique pour toutes les installations.
- Pas d'authentification du message (pas de MAC/HMAC), CBC sans intégrité est vulnérable au padding oracle et aux attaques de type bit-flipping.

### 3.5 Modification automatique du firewall — ÉLEVÉ/CRITIQUE

```@c:\Users\yoann\devin\Mark\Mark-XLVI\dashboard\server.py:99-232
```

Le programme demande l'élévation UAC et ouvre le port 8000/8001 à l'écoute publique (`host="0.0.0.0"`). Sur réseau non fiable, cela expose l'interface de contrôle complet du PC.

## 4. Risques de confidentialité et de données

### 4.1 Capture d'écran et webcam

`screen_processor.py` capture l'écran ou la webcam et envoie l'image à Gemini. Aucun consentement explicite, aucune indication visuelle pendant la capture.

### 4.2 Historique de conversation en mémoire

`dashboard/server.py:437-448` conserve les 300 derniers messages en mémoire. Aucune rotation ou chiffrement au repos.

### 4.3 Fichiers uploadés accessibles

Les uploads sont stockés dans `~/Downloads/JARVIS Uploads` ou `~/Documents/JARVIS Uploads` (`dashboard/server.py:44-59`) et servis par le serveur web à quiconque possède le token.

## 6. Risques liés à Playwright

`actions/browser_control.py` utilise Playwright pour piloter des navigateurs avec les profils utilisateurs réels.

### 6.1 Profils navigateurs réels

Le code tente de localiser et d'utiliser les profils Chrome, Edge, Firefox, Opera, Brave, Vivaldi de l'utilisateur (`actions/browser_control.py:150-250`). Cela signifie que l'assistant peut accéder aux cookies, sessions, mots de passe enregistrés et historique de navigation.

### 6.2 Pas de sandbox dédié

Playwright est lancé en mode non-headless ou avec des profils persistants. Si le LLM demande de naviguer vers un site malveillant, le navigateur exécute du JavaScript avec les cookies de l'utilisateur connecté. Aucune isolation de réseau (proxy, DNS filtré) n'est configurée.

### 6.3 Téléchargements de fichiers

`actions/browser_control.py` peut déclencher des téléchargements (`download` event) et les stocker dans le répertoire de l'utilisateur. Aucune vérification de contenu n'est effectuée.

### 6.4 Injection de code dans le navigateur

L'outil peut exécuter du JavaScript arbitraire via `page.evaluate()` (implicite dans les actions `type`, `click`, `fill_form`). Un site contrôlé par un attaquant peut manipuler le DOM pour déclencher des actions non intentionnelles.

## 7. Risques liés à PyAutoGUI

`actions/computer_control.py`, `actions/send_message.py`, `actions/computer_settings.py` et `actions/desktop.py` utilisent PyAutoGUI pour simuler clavier/souris.

### 7.1 Prise de contrôle du poste de travail

PyAutoGUI envoie des événements au niveau du système. Le LLM peut théoriquement :
- Ouvrir un terminal (`win + R`, `cmd`)
- Taper des commandes arbitraires
- Confirmer des dialogues UAC par clic coordonné
- Copier/coller des données sensibles via le presse-papiers

### 7.2 Fragilité et effets de bord

Les actions reposent sur des temporisations fixes (`time.sleep(0.5)`, `time.sleep(2.5)`). Si une fenêtre ne répond pas ou si le focus change, l'action peut interagir avec la mauvaise application. Cela peut entraîner des suppressions ou des envois de messages involontaires.

### 7.3 Pas de confirmation utilisateur

Aucune action PyAutoGUI ne demande de confirmation explicite. Une commande vocale comme "envoie ce message à mon patron" est exécutée directement.

## 8. Vulnérabilités potentielles supplémentaires

### 8.1 Path traversal dans les uploads

```@c:\Users\yoann\devin\Mark\Mark-XLVI\dashboard\server.py:711-721
@app.get("/uploads/{filename}")
async def download_file(filename: str, token: str = ""):
```

La fonction `_safe_filename` filtre les `/` et `\` mais peut être contournée si le répertoire d'upload est configurable (`dashboard/server.py:44-59`). Un attaquant avec un token peut tenter de lire des fichiers hors du répertoire d'upload.

### 8.2 SSRF via le navigateur

`browser_control` peut être utilisé pour accéder à des services internes (`http://localhost`, `http://127.0.0.1`, `http://192.168.x.x`). Le LLM peut être incité à scanner le réseau local ou interagir avec des services non exposés.

### 8.3 Fuite de données par le prompt

La mémoire long terme et les captures d'écran sont envoyées à Gemini. Si le LLM est "jailbreaké", il peut être amené à répéter des informations sensibles dans la réponse audio ou dans les logs.

### 8.4 Consommation de ressources non limitée

`dev_agent.py` et `code_helper.py` peuvent générer et exécuter des projets de taille arbitraire. Aucune limite de disque, de mémoire ou de CPU n'est imposée. Une boucle infinie générée par le LLM peut bloquer le système.

### 8.5 Élévation de privilèges via le firewall

Le script `.bat` généré pour Windows (`dashboard/server.py:183-186`) est exécuté avec `shell=True`. Si le fichier est modifié entre son écriture et son exécution, ou si le chemin est prévisible, un attaquant local peut injecter des commandes.

### 8.6 Fuite de clé API par les logs

`main.py:576` et `actions/desktop.py` impriment des arguments d'outils dans `print()`. Si un argument contient la clé API (via un prompt utilisateur), elle peut apparaître dans les logs console.

## 9. Classement CVSS approximatif

> Les scores CVSS 3.1 sont des estimations basées sur l'analyse statique. Un audit dynamique affinerait ces valeurs.

| # | Vulnérabilité | Vecteur CVSS 3.1 approximatif | Score | Sévérité |
|---|---|---|---|---|
| 1 | Clé privée SSL commitée en clair | `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N` | **9.1** | Critique |
| 2 | RCE via `exec()` de code LLM | `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H` | **9.8** | Critique |
| 3 | Injection de commandes `shell=True` (`open_app`) | `CVSS:3.1/AV:L/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H` | **8.4** | Élevée |
| 4 | Stockage clair de la clé API Gemini | `CVSS:3.1/AV:L/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N` | **6.5** | Moyenne |
| 5 | Authentification dashboard par PIN 6 chiffres sans rate limit | `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N` | **9.1** | Critique |
| 6 | Chiffrement AES maison sans intégrité | `CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:N` | **7.4** | Élevée |
| 7 | Modification automatique du firewall + exposition 0.0.0.0 | `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H` | **9.8** | Critique |
| 8 | Upload/serve de fichiers sans contrôle de type | `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:H/A:H` | **8.2** | Élevée |
| 9 | Path traversal potentiel dans `/uploads/{filename}` | `CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:N/A:N` | **5.3** | Moyenne |
| 10 | Prise de contrôle via PyAutoGUI | `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H` | **9.8** | Critique |
| 11 | Exécution de scripts générés sur le Desktop (`code_helper`) | `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H` | **9.8** | Critique |
| 12 | Accès aux profils navigateurs via Playwright | `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N` | **7.5** | Élevée |
| 13 | Fuite de données par prompts/jailbreak | `CVSS:3.1/AV:N/AC:H/PR:N/UI:R/S:U/C:H/I:N/A:N` | **5.7** | Moyenne |
| 14 | Dépendances sans versions / auto-install pip | `CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:H` | **7.7** | Élevée |
| 15 | Capture d'écran/webcam sans indicateur | `CVSS:3.1/AV:L/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N` | **6.5** | Moyenne |

## 10. Dépendances et vulnérabilités potentielles

### 10.1 Dépendances sans version fixée

`requirements.txt` ne fixe **aucune** version :

```@c:\Users\yoann\devin\Mark\Mark-XLVI\requirements.txt:1-28
sounddevice
google-genai
google-generativeai
pillow
requests
...
```

Cela expose le projet à des ruptures de compatibilité et à des versions vulnérables.

### 10.2 Dépendances en conflit

`google-genai` et `google-generativeai` sont deux SDK distincts pour accéder à Gemini. Le code utilise `google-genai` (`main.py:11`), mais `google-generativeai` est aussi listé. Cela alourdit l'installation et peut créer des conflits.

### 10.3 Dépendances optionnelles manquantes dans requirements.txt

Plusieurs paquets sont référencés dans le code mais absents de `requirements.txt` (installés à la demande par `core/installer.py`) :

- `faster-whisper`, `vosk`
- `edge-tts`, `kokoro`, `soundfile`, `miniaudio`
- `torch` (si CUDA)
- `pandas`, `openpyxl`, `python-docx`, `pydub` (pour `file_processor.py`)

Cette approche est fragile : le premier lancement peut échouer si le réseau est indisponible.

## 11. Permissions et élévation de privilèges

- Le programme demande régulièrement l'**administrateur** pour modifier le firewall (`dashboard/server.py:183-232`).
- `computer_settings.py` peut exécuter `shutdown`, `restart`, `sleep`, modifier le volume/la luminosité, le WiFi.
- `actions/computer_control.py` et `actions/computer_settings.py` utilisent `pyautogui` pour des actions système sensibles.

Combiné au RCE potentiel (section 2), cela signifie que n'importe quelle commande vocale interprétée par Gemini peut théoriquement déclencher une action système de haut niveau.

## 12. Vérifications de sécurité absentes

| Contrôle | Statut |
|---|---|
| Gestion centralisée de secrets | ❌ Absente |
| Chiffrement des données sensibles au repos | ❌ Absent |
| Validation/sanitation des entrées utilisateur | ⚠️ Partielle (path, screenshot) |
| Rate limiting / brute force PIN | ❌ Absent |
| Logs d'audit sécurisés | ❌ Absent |
| Scan de fichiers uploadés | ❌ Absent |
| Signature des exécutables/scripts | ❌ Absent |
| SBOM / audit des dépendances | ❌ Absent |
| Tests de sécurité | ❌ Absent |

## 13. Synthèse des risques

| Vulnérabilité | Fichier(s) | Criticité |
|---|---|---|
| Clé privée SSL commitée | `config/certs/jarvis.key` | **Critique** |
| RCE via `exec()` de code LLM | `actions/desktop.py` | **Critique** |
| Injection de commandes `shell=True` | `actions/open_app.py`, `dashboard/server.py`, `actions/computer_settings.py`, `actions/dev_agent.py` | **Élevée** |
| Stockage clair de la clé API | `memory/config_manager.py`, `main.py` | **Élevée** |
| Authentification faible (PIN 6 chiffres) | `dashboard/server.py` | **Élevée** |
| Chiffrement maison (AES-CBC sans intégrité) | `dashboard/server.py` | **Élevée** |
| Modification auto du firewall | `dashboard/server.py` | **Élevée** |
| Upload/serve de fichiers sans contrôle | `dashboard/server.py` | **Élevée** |
| Dépendances sans versions / auto-install | `requirements.txt`, `core/installer.py`, `core/tts.py` | **Moyenne** |
| Dépendances optionnelles non déclarées | `requirements.txt`, `actions/file_processor.py` | **Moyenne** |
| Capture écran/webcam sans indicateur | `actions/screen_processor.py` | **Moyenne** |
| Historique conservé en mémoire | `dashboard/server.py` | **Faible** |
