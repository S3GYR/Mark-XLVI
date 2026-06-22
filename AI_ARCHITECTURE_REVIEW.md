# Revue d'architecture IA — MARK XLVI

> Ce document analyse l'architecture d'intelligence artificielle du projet d'un point de vue d'architecte logiciel et d'ingénieur IA, avec une perspective production.

## 1. Analyse de l'intégration Gemini

### 1.1 Modèle utilisé

`main.py` se connecte à l'API **Gemini Live** via le SDK `google-genai` :

```@c:\Users\yoann\devin\Mark\Mark-XLVI\main.py:46-50
LIVE_MODEL          = "models/gemini-2.5-flash-native-audio-preview-12-2025"
CHANNELS            = 1
SEND_SAMPLE_RATE    = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE          = 1024
```

```@c:\Users\yoann\devin\Mark\Mark-XLVI\main.py:893-896
client = genai.Client(
    api_key=_get_api_key(),
    http_options={"api_version": "v1beta"}
)
```

```@c:\Users\yoann\devin\Mark\Mark-XLVI\main.py:916-918
async with (
    client.aio.live.connect(model=LIVE_MODEL, config=config) as session,
    asyncio.TaskGroup() as tg,
):
```

Le modèle est choisi pour le **multimodal natif audio** : il reçoit du PCM 16 kHz et renvoie du PCM 24 kHz. Cela évite d'implémenter une chaîne STT → LLM → TTS séparée.

### 1.2 Configuration de la session

La configuration (`types.LiveConnectConfig`) est construite dans `_build_config` (`main.py:535-569`) :

- `response_modalities=["AUDIO"]` : l'assistant répond toujours en audio natif.
- `output_audio_transcription` et `input_audio_transcription` : transcriptions automatiques.
- `system_instruction` : prompt système + date/heure + mémoire long terme.
- `tools` : déclarations des 17 outils (`TOOL_DECLARATIONS`).
- `session_resumption` : activé (`types.SessionResumptionConfig()`).
- `speech_config` : voix `Charon`.

### 1.3 Déclaration et exécution des outils

Les outils sont déclarés manuellement dans `main.py:74-466` sous forme de JSON fonctionnel. L'exécution se fait dans `_execute_tool` (`main.py:571-697`) qui dispatche vers les modules `actions/`.

### 1.4 Points forts de l'intégration Gemini

- **Pipeline audio natif** : pas de STT/TTS intermédiaire, latence réduite.
- **Multimodal** : capture d'écran et webcam envoyées directement au modèle (`screen_processor.py`).
- **Streaming** : réponse audio en temps réel avec `_receive_audio` et `_play_audio` (`main.py:733-834`).
- **Resumption** : la session peut être reprise en cas de déconnexion.

### 1.5 Points faibles de l'intégration Gemini

- **Dépendance unique** : tout le système est calé sur `google-genai`. Si Google modifie l'API ou augmente les tarifs, le projet est bloqué.
- **Version bêta** : `http_options={"api_version": "v1beta"}` indique une API instable.
- **Pas de fallback** : si Gemini est indisponible, l'assistant cesse de fonctionner. Il n'y a pas de fallback vers un autre modèle.
- **Pas de streaming des tool calls** : les outils sont exécutés de manière synchrone dans `run_in_executor`, ce qui bloque temporairement le flux.
- **Pas de gestion du contexte** : la mémoire est injectée à chaque connexion via `system_instruction`. Il n'y a pas de mémoire conversationnelle dynamique.

## 2. Analyse de la mémoire

### 2.1 Architecture de la mémoire

La mémoire long terme est stockée dans un fichier JSON unique : `memory/long_term.json`.

```@c:\Users\yoann\devin\Mark\Mark-XLVI\memory\memory_manager.py:14-18
MEMORY_PATH = BASE_DIR / "memory" / "long_term.json"
MEMORY_MAX_CHARS = 2200
```

```@c:\Users\yoann\devin\Mark\Mark-XLVI\memory\memory_manager.py:20-27
_CATEGORIES = {
    "identity": {},
    "preferences": {},
    "projects": {},
    "relationships": {},
    "wishes": {},
    "notes": {},
}
```

### 2.2 Fonctionnement

- `load_memory()` lit le fichier JSON (`memory/memory_manager.py:30-37`).
- `update_memory()` fusionne récursivement les nouvelles entrées (`memory/memory_manager.py:111-118`).
- `format_memory_for_prompt()` formate la mémoire en texte pour le prompt système (`memory/memory_manager.py:120-135`).
- `trim_memory()` tronque la mémoire si elle dépasse `MEMORY_MAX_CHARS` (`memory/memory_manager.py:58-68`).

### 2.3 Limites de la mémoire actuelle

| Limite | Impact |
|---|---|
| Capacité fixe à 2200 caractères | Perte d'informations anciennes |
| Pas de recherche sémantique | Le LLM ne peut pas retrouver une info par similarité |
| Pas de hiérarchie temporelle | Impossible de pondérer les faits récents |
| Stockage JSON plat | Pas de relations, pas de métadonnées |
| Pas d'embedding | Pas de mémoire vectorielle |
| Pas de backup/versioning | Corruption = perte totale |
| Mise à jour par écrasement complet | Risque de concurrence si processus multiples |

### 2.4 Mémoire conversationnelle

Il n'y a **pas** de mémoire conversationnelle explicite. Les messages ne sont pas conservés entre les sessions Gemini Live (hormis la mémoire long terme). Chaque reconnexion repart avec un nouveau `system_instruction`.

## 3. Limites du système actuel

### 3.1 Monomodèle et mono-fournisseur

MARK XLVI est verrouillé sur Gemini. Il n'y a pas d'abstraction LLM. `core/llm_client.py` existe mais n'est pas utilisé par `main.py`.

### 3.2 Pas de gestion avancée des tool calls

- Les outils sont déclarés manuellement en JSON.
- Pas de validation automatique des arguments.
- Pas de retries sur les tool calls.
- Pas de traçabilité des appels.

### 3.3 Pas de chaîne de raisonnement (Reasoning)

Le modèle est utilisé en mode "action direct". Il n'y a pas de boucle de réflexion interne, de planification multi-étapes, ou d'agent autonome avec mémoire de travail.

### 3.4 Pas de personnalisation du modèle

La température, le top-p, la fréquence de penalty, etc. ne sont pas configurables. Seule la voix (`Charon`) et les modalités sont réglées.

### 3.5 Pas de gestion des coûts / quotas

Aucun compteur de tokens, de minutes audio, ou de requêtes API. Aucune limitation du nombre de tool calls.

### 3.6 Pas de sécurité LLM

Aucun mécanisme de détection de jailbreak, d'injection de prompt, ou de filtrage des sorties. La mémoire et les captures d'écran sont envoyées sans anonymisation.

## 4. Possibilité de migration vers d'autres fournisseurs

### 4.1 LiteLLM

**Faisabilité : Élevée**

LiteLLM offre une interface unifiée pour OpenAI, Anthropic, Gemini, Ollama, Mistral, DeepSeek, etc. C'est la solution la plus simple pour unifier les appels.

- **Avantages** : un seul SDK, gestion des modèles, routing, retries, observabilité.
- **Inconvénients** : le modèle audio natif de Gemini Live n'est pas encore supporté par LiteLLM de manière équivalente. Il faudrait probablement revenir à un pipeline STT → LLM texte → TTS.
- **Migration** : remplacer `genai.Client.aio.live.connect` par `litellm.acompletion` avec streaming audio via un modèle de TTS.
- **Effort** : Moyen (1-2 mois) si on garde du texte, Important (3-4 mois) si on veut conserver l'expérience audio temps réel.

### 4.2 Ollama

**Faisabilité : Moyenne**

`core/llm_client.py` implémente déjà un client Ollama (`core/llm_client.py:1-587`).

- **Avantages** : exécution locale, pas de coût API, confidentialité.
- **Inconvénients** : pas de modèle audio natif comparable, nécessite un GPU puissant pour la qualité, pas de tool calling aussi robuste que Gemini.
- **Migration** : utiliser `core/llm_client.py` et brancher un pipeline STT (`core/stt.py`) + LLM local + TTS (`core/tts.py`).
- **Effort** : Moyen (2-3 mois) pour une version textuelle locale, Important (4-6 mois) pour une expérience multimodale.

### 4.3 OpenAI

**Faisabilité : Élevée**

OpenAI propose GPT-4o avec audio natif (Realtime API) et GPT-4o-mini pour le texte.

- **Avantages** : qualité, tool calling fiable, Realtime API pour l'audio natif.
- **Inconvénients** : coût élevé, dépendance à un fournisseur unique.
- **Migration** : remplacer `genai.Client` par `openai.AsyncOpenAI` et adapter le format des tool calls.
- **Effort** : Moyen (1-2 mois).

### 4.4 Anthropic

**Faisabilité : Moyenne**

Anthropic Claude 3.5/4 Sonnet est excellent en tool calling et en raisonnement, mais ne propose pas d'audio natif.

- **Avantages** : qualité du raisonnement, sécurité (constitutionnal AI), tool calling robuste.
- **Inconvénients** : pas d'audio natif, pas de streaming audio.
- **Migration** : pipeline STT → Claude → TTS. Adapter le format de tool calls (XML/JSON).
- **Effort** : Moyen (2-3 mois).

### 4.5 DeepSeek

**Faisabilité : Moyenne**

DeepSeek offre des modèles compétitifs en OpenAI-compatible API.

- **Avantages** : coût faible, bonnes performances en coding/raisonnement.
- **Inconvénients** : pas d'audio natif, disponibilité variable, questions de confidentialité selon l'hébergement.
- **Migration** : utiliser le format OpenAI-compatible. Nécessite un pipeline STT/TTS.
- **Effort** : Moyen (1-2 mois).

### 4.6 Mistral

**Faisabilité : Moyenne**

Mistral offre des modèles via API et des modèles open source (Mistral 7B, Mixtral, Codestral).

- **Avantages** : modèles open source disponibles, bon tool calling avec les grands modèles.
- **Inconvénients** : pas d'audio natif, les petits modèles ne gèrent pas bien 17 outils.
- **Migration** : API Mistral ou self-host via Ollama/vLLM. Pipeline STT/TTS.
- **Effort** : Moyen (2-3 mois).

## 5. Faisabilité d'un mode multi-modèles

### 5.1 Architecture cible recommandée

```
┌─────────────────────────────────────────┐
│          LLM Gateway / Router           │
│   (LiteLLM, ou abstraction interne)     │
└──────────────┬──────────────────────────┘
               │
    ┌──────────┼──────────┐
    ▼          ▼          ▼
Gemini      OpenAI      Ollama
  │            │            │
  ▼            ▼            ▼
Audio natif  Realtime API  Text + STT/TTS
```

### 5.2 Stratégie de routing

| Usage | Modèle recommandé | Pourquoi |
|---|---|---|
| Conversation audio temps réel | Gemini Live ou OpenAI Realtime | Audio natif, faible latence |
| Tâches complexes / raisonnement | Claude 3.5 Sonnet / GPT-4o | Meilleure planification |
| Génération de code | Claude 3.5 Sonnet / DeepSeek V3 / Codestral | Qualité du code |
| Exécution locale / confidentialité | Ollama + Llama 3 / Mistral | Pas de données dans le cloud |
| Résumé rapide / simple | Gemini Flash / GPT-4o-mini | Coût et latence |

### 5.3 Faisabilité technique

**Faisable, mais avec des efforts importants.** Les principaux défis sont :

1. **Différence de formats** : chaque API a son propre format de tool calls (OpenAI, Anthropic, Gemini).
2. **Audio natif** : seuls Gemini Live et OpenAI Realtime offrent une expérience audio temps réel native. Les autres nécessitent un pipeline STT/TTS plus complexe.
3. **Gestion des coûts** : le routing doit tenir compte du coût par token et par minute audio.
4. **Observabilité** : chaque modèle doit être tracé (logs, latence, coût, qualité).
5. **Sécurité** : les secrets de chaque fournisseur doivent être gérés séparément.

### 5.4 Recommandation

Pour une production quotidienne, je recommande :

- **Phase 1** : garder Gemini Live comme modèle principal, mais **extraire une abstraction `LLMClient`** dans `core/llm_client.py` ou un nouveau module `jarvis/llm/`.
- **Phase 2** : ajouter **OpenAI Realtime API** comme fallback audio natif.
- **Phase 3** : ajouter **Anthropic Claude** pour les tâches de raisonnement complexe via un pipeline textuel STT/TTS.
- **Phase 4** : intégrer **Ollama** comme option offline via LiteLLM ou l'interface existante de `core/llm_client.py`.

## 6. Recommandations pour la mémoire

### 6.1 Court terme

- Augmenter `MEMORY_MAX_CHARS` ou remplacer la troncature par une stratégie de pertinence.
- Ajouter une sauvegarde automatique (`long_term.json.bak`).
- Déplacer le fichier hors du répertoire source (`platformdirs`).

### 6.2 Moyen terme

- Remplacer le JSON par **SQLite** avec une table `memories` indexée par catégorie et date.
- Ajouter des embeddings via `sentence-transformers` ou l'API Gemini Embedding.
- Implémenter une recherche sémantique pour récupérer les faits pertinents avant chaque appel.

### 6.3 Long terme

- Adopter une base vectorielle légère comme **Chroma** ou **Qdrant** (ou **sqlite-vec**).
- Structurer la mémoire en entités/relations (RAG knowledge graph).
- Ajouter une mémoire épisodique (historique des conversations) avec résumé automatique.

## 7. Verdict IA

| Critère | État actuel | Objectif production |
|---|---|---|
| Fournisseur | Verrouillé Gemini | Multi-fournisseurs avec fallback |
| Audio natif | ✅ Oui (Gemini Live) | ✅ Oui + fallback OpenAI Realtime |
| Tool calling | Basique, manuel | Déclaratif, validé, tracé |
| Mémoire | JSON plat, 2200 car | Base vectorielle + sémantique |
| Sécurité LLM | Absente | Jailbreak detection, anonymisation |
| Observabilité | Aucune | Logs, coûts, latence, qualité |
| Multi-modèle | Non | Oui, avec router |
| Local/offline | Non | Oui, via Ollama |

## 8. Citations clés

- Modèle Gemini Live : `main.py:46`, `main.py:893-918`
- Configuration session : `main.py:535-569`
- Déclarations outils : `main.py:74-466`
- Exécution outils : `main.py:571-697`
- Mémoire JSON : `memory/memory_manager.py:14-68`, `memory/memory_manager.py:111-135`
- Client Ollama existant : `core/llm_client.py:1-587`
- Pipeline audio : `main.py:704-834`
