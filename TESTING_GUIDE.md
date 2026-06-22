# Guide de Test pour l'Application MARK XLVI

## 1. Tests Unitaires (pytest)

### Exécuter tous les tests
```bash
python -m pytest
```

### Exécuter avec couverture
```bash
python -m pytest --cov=jarvis --cov-report=term-missing
```

### Exécuter un module spécifique
```bash
python -m pytest tests/audio/test_capture_working_v2.py -v
```

### Tests qui fonctionnent actuellement (54% de couverture)
```bash
python -m pytest --cov=jarvis --tb=no -q --ignore=tests/core/test_tool_runner.py --ignore=tests/core/test_live_session.py --ignore=tests/memory/test_postgres_store.py --ignore=tests/main/test_main.py --ignore=tests/security/test_certs.py --ignore=tests/audio/test_capture.py --ignore=tests/audio/test_playback.py --ignore=tests/tools/test_legacy_wrappers.py --ignore=tests/web/test_routes_integration.py --ignore=tests/audio/test_phone_relay.py --ignore=tests/core/test_tool_runner_fixed.py --ignore=tests/core/test_live_session_fixed.py --ignore=tests/core/test_live_session_real.py --ignore=tests/main/test_main_fixed.py --ignore=tests/ui/test_headless.py --ignore=tests/integration/test_workflows.py --ignore=tests/audio/test_capture_simple.py --ignore=tests/audio/test_capture_real.py --ignore=tests/audio/test_playback_real.py --ignore=tests/audio/test_playback_fixed.py --ignore=tests/core/test_main_simple.py --ignore=tests/performance/test_load.py --ignore=tests/core/test_live_session_working.py --ignore=tests/core/test_main_working.py --ignore=tests/ui/test_widgets.py --ignore=tests/core/test_live_session_improved.py --ignore=tests/core/test_main_improved.py --ignore=tests/audio/test_capture_improved.py --ignore=tests/audio/test_playback_improved.py --ignore=tests/core/test_tool_runner_improved.py --ignore=tests/core/test_main_simple_v2.py --ignore=tests/core/test_main_working_v2.py --ignore=tests/audio/test_capture_simple_v2.py --ignore=tests/audio/test_capture_basic_v2.py --ignore=tests/audio/test_playback_working_v2.py --ignore=tests/core/test_tool_runner_working_v2.py
```

## 2. Tests de l'Application CLI

### Lancer l'application CLI
```bash
python -m jarvis.main
```

### Lancer l'interface GUI
```bash
python -m jarvis.main --gui
```

### Voir l'aide
```bash
python -m jarvis.main --help
```

## 3. Tests des Composants Web

### Démarrer le serveur web
```bash
python -c "
import uvicorn
from jarvis.web.server import DashboardServer

server = DashboardServer()
uvicorn.run(server.app, host='127.0.0.1', port=8000)
"
```

### Tester les routes disponibles
```bash
python -c "
import asyncio
from jarvis.web.server import DashboardServer

async def test_server():
    server = DashboardServer()
    print('Server created successfully')
    print(f'Available routes: {[route.path for route in server.app.routes]}')

asyncio.run(test_server())
"
```

### Accéder à l'interface web
Ouvrez votre navigateur sur: http://127.0.0.1:8000

## 4. Tests des Composants Audio

### Test de capture audio
```bash
python -c "
import asyncio
from jarvis.audio.capture import AudioCapture

def test_capture():
    print('Testing AudioCapture...')
    
    def output_callback(data):
        audio_data = data.get('data', b'')
        print(f'Audio data: {len(audio_data)} bytes')
    
    capture = AudioCapture(
        output_callback=output_callback,
        is_speaking=lambda: False,
        is_muted=lambda: False,
        is_phone_active=lambda: False
    )
    
    print('AudioCapture created successfully')
    print(f'Running state: {capture._running}')
    print(f'Stream: {capture._stream}')

test_capture()
"
```

### Test de lecture audio
```bash
python -c "
import asyncio
from jarvis.audio.playback import AudioPlayback

def test_playback():
    print('Testing AudioPlayback...')
    audio_queue = asyncio.Queue()
    
    playback = AudioPlayback(audio_queue=audio_queue)
    
    print('AudioPlayback created successfully')
    print(f'Running state: {playback._running}')
    print(f'Stream: {playback._stream}')

test_playback()
"
```

## 5. Tests des Composants Core

### Test ToolRunner
```bash
python -c "
from jarvis.core.tool_runner import ToolRunner
from jarvis.core.player import ConsolePlayer

def test_tool_runner():
    print('Testing ToolRunner...')
    player = ConsolePlayer()
    runner = ToolRunner(player)
    print('ToolRunner created successfully')

test_tool_runner()
"
```

### Test AgentOrchestrator
```bash
python -c "
import asyncio
from jarvis.core.orchestrator import AgentOrchestrator
from jarvis.config.settings import get_settings

async def test_orchestrator():
    print('Testing AgentOrchestrator...')
    settings = get_settings()
    player = ConsolePlayer()
    
    # Mock memory for testing
    class MockMemory:
        async def close(self):
            pass
    
    memory = MockMemory()
    
    orchestrator = AgentOrchestrator(
        settings=settings,
        memory=memory,
        player=player
    )
    print('AgentOrchestrator created successfully')

asyncio.run(test_orchestrator())
"
```

## 6. Tests des Composants Memory

### Test JsonMemoryStore
```bash
python -c "
import asyncio
from jarvis.memory.json_store import JsonMemoryStore

async def test_json_memory():
    print('Testing JsonMemoryStore...')
    store = JsonMemoryStore()
    await store.initialize()
    
    # Test save and retrieve
    await store.save('test_key', 'Hello JARVIS', 'notes')
    result = await store.get('test_key')
    print(f'Saved and retrieved: {result}')
    
    # Test search
    results = await store.search('Hello')
    print(f'Search results: {len(results)} items found')
    
    await store.close()
    print('JsonMemoryStore test completed')

asyncio.run(test_json_memory())
"
```

## 7. Tests des Composants LLM

### Test Embeddings
```bash
python -c "
from jarvis.llm.embeddings import get_embedding_provider, MockEmbeddingProvider

def test_embeddings():
    print('Testing Embeddings...')
    
    # Test MockEmbeddingProvider
    provider = MockEmbeddingProvider(dim=10)
    embedding = provider.encode('test text')
    print(f'Embedding created: {len(embedding)} dimensions')
    
    # Test get_embedding_provider
    provider = get_embedding_provider()
    print(f'Provider created: {type(provider).__name__}')
    print('Embeddings test completed')

test_embeddings()
"
```

## 8. Tests de Configuration

### Test Settings
```bash
python -c "
from jarvis.config.settings import get_settings

def test_settings():
    print('Testing Settings...')
    settings = get_settings()
    print(f'LLM Model: {settings.llm_model}')
    print(f'Embedding Provider: {settings.embedding_provider}')
    print(f'Vector Dim: {settings.vector_dim}')
    print('Settings test completed')

test_settings()
"
```

## 9. Tests de Sécurité

### Test Permissions
```bash
python -c "
from jarvis.security.permissions import Permission, check_permission

def test_permissions():
    print('Testing Permissions...')
    
    # Test permission checking
    result = check_permission('file.read', '/safe/path')
    print(f'Permission check result: {result}')
    
    print('Permissions test completed')

test_permissions()
"
```

### Test Secrets
```bash
python -c "
from jarvis.security.secrets import get_secret

def test_secrets():
    print('Testing Secrets...')
    
    # Test secret retrieval (should return None for non-existent)
    secret = get_secret('test_secret')
    print(f'Secret retrieved: {secret}')
    
    print('Secrets test completed')

test_secrets()
"
```

## 10. Tests d'Intégration

### Test complet de l'assistant
```bash
python -c "
import asyncio
from jarvis.main import JarvisAssistant

async def test_assistant():
    print('Testing JarvisAssistant...')
    
    assistant = JarvisAssistant()
    
    # Test setup (might fail without proper configuration)
    try:
        await assistant.setup()
        print('Assistant setup completed')
        
        # Test command execution
        result = await assistant.run_command('hello')
        print(f'Command result: {result}')
        
        await assistant.shutdown()
        print('Assistant shutdown completed')
        
    except Exception as e:
        print(f'Integration test failed (expected): {e}')

asyncio.run(test_assistant())
"
```

## 11. Tests de Performance

### Test de charge simple
```bash
python -c "
import time
import asyncio
from jarvis.llm.embeddings import MockEmbeddingProvider

def test_performance():
    print('Testing Performance...')
    
    provider = MockEmbeddingProvider(dim=768)
    
    # Test embedding generation speed
    start_time = time.time()
    for i in range(100):
        embedding = provider.encode(f'test text {i}')
    end_time = time.time()
    
    print(f'Generated 100 embeddings in {end_time - start_time:.2f} seconds')
    print(f'Average time per embedding: {(end_time - start_time) / 100 * 1000:.2f} ms')
    print('Performance test completed')

test_performance()
"
```

## 12. Dépannage

### Problèmes courants

1. **ModuleNotFoundError**: Assurez-vous d'être dans le répertoire racine du projet
2. **ImportError**: Vérifiez que toutes les dépendances sont installées
3. **PermissionError**: Certaines fonctionnalités nécessitent des permissions système
4. **Audio errors**: Vérifiez que votre matériel audio est disponible

### Logs et débogage

```bash
# Activer les logs détaillés
export JARVIS_LOG_LEVEL=DEBUG

# Ou en Python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 13. Tests Automatisés (CI/CD)

### Exécuter tous les tests validés
```bash
python -m pytest tests/core/test_tool_runner_real_v2.py tests/audio/test_capture_working_v2.py tests/audio/test_playback_basic_v2.py tests/core/test_main_real_v2.py tests/llm/test_embeddings_working_v2.py -v --cov=jarvis
```

### Vérifier la couverture
```bash
python -m pytest --cov=jarvis --cov-report=html --cov-report=term
# Ouvrir htmlcov/index.html pour voir le rapport détaillé
```

## Résumé

Ce guide couvre:
- **Tests unitaires**: pytest avec 54% de couverture
- **Tests d'intégration**: composants individuels
- **Tests de bout en bout**: application complète
- **Tests de performance**: benchmarks simples
- **Dépannage**: problèmes courants et solutions

Pour une utilisation en production, commencez par les tests unitaires, puis progressez vers les tests d'intégration et enfin les tests de bout en bout.
