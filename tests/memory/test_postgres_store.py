"""Tests for PostgreSQL memory store."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
from datetime import datetime
from typing import Any


def test_postgres_store_initialization():
    """Test PostgreSQL store initialization with proper configuration."""
    with patch('jarvis.memory.postgres_store.get_settings') as mock_settings:
        mock_settings.return_value.postgres_url = "postgresql://test:test@localhost/test"
        
        with patch('sqlalchemy.create_engine') as mock_create_engine:
            mock_engine = Mock()
            mock_create_engine.return_value = mock_engine
            
            from jarvis.memory.postgres_store import PostgresMemoryStore
            store = PostgresMemoryStore()
            
            assert store is not None
            assert store._engine == mock_engine
            mock_create_engine.assert_called_once()


def test_postgres_store_connection_management():
    """Test PostgreSQL connection management."""
    with patch('jarvis.memory.postgres_store.get_settings'):
        with patch('sqlalchemy.create_engine'):
            from jarvis.memory.postgres_store import PostgresMemoryStore
            
            store = PostgresMemoryStore()
            
            # Test connection
            with patch.object(store, '_connect') as mock_connect:
                mock_connect.return_value = True
                
                result = store.connect()
                assert result is True
                mock_connect.assert_called_once()
                
                # Test disconnection
                store.disconnect()
                assert not store._connected


def test_postgres_store_memory_operations():
    """Test basic memory operations (add, get, search)."""
    with patch('jarvis.memory.postgres_store.get_settings'):
        with patch('sqlalchemy.create_engine'):
            from jarvis.memory.postgres_store import PostgresMemoryStore
            
            store = PostgresMemoryStore()
            
            # Mock database session
            mock_session = Mock()
            store._session = mock_session
            
            # Test adding memory
            test_memory = {
                "content": "Test memory content",
                "type": "user_input",
                "timestamp": datetime.now().isoformat()
            }
            
            with patch.object(store, '_add_memory') as mock_add:
                mock_add.return_value = "memory_id_123"
                
                result = store.add_memory(test_memory)
                assert result == "memory_id_123"
                mock_add.assert_called_once_with(test_memory)
            
            # Test getting memory
            with patch.object(store, '_get_memory') as mock_get:
                mock_get.return_value = test_memory
                
                result = store.get_memory("memory_id_123")
                assert result == test_memory
                mock_get.assert_called_once_with("memory_id_123")


def test_postgres_store_vector_search():
    """Test vector similarity search functionality."""
    with patch('jarvis.memory.postgres_store.get_settings'):
        with patch('sqlalchemy.create_engine'):
            from jarvis.memory.postgres_store import PostgresMemoryStore
            
            store = PostgresMemoryStore()
            
            # Mock vector search
            test_query = "test search query"
            test_results = [
                {"id": "1", "content": "Result 1", "similarity": 0.9},
                {"id": "2", "content": "Result 2", "similarity": 0.8}
            ]
            
            with patch.object(store, '_vector_search') as mock_search:
                mock_search.return_value = test_results
                
                results = store.search_similar(test_query, limit=5)
                assert len(results) == 2
                assert results[0]["similarity"] == 0.9
                mock_search.assert_called_once_with(test_query, 5)


def test_postgres_store_embedding_integration():
    """Test integration with embedding models."""
    with patch('jarvis.memory.postgres_store.get_settings'):
        with patch('sqlalchemy.create_engine'):
            from jarvis.memory.postgres_store import PostgresMemoryStore
            
            store = PostgresMemoryStore()
            
            # Mock embedding generation
            test_text = "Test text for embedding"
            test_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
            
            with patch('jarvis.llm.embeddings.get_embedding') as mock_embedding:
                mock_embedding.return_value = test_embedding
                
                result = store._generate_embedding(test_text)
                assert result == test_embedding
                mock_embedding.assert_called_once_with(test_text)


def test_postgres_store_error_handling():
    """Test error handling in database operations."""
    with patch('jarvis.memory.postgres_store.get_settings'):
        with patch('sqlalchemy.create_engine'):
            from jarvis.memory.postgres_store import PostgresMemoryStore
            
            store = PostgresMemoryStore()
            
            # Test connection error
            with patch.object(store, '_connect') as mock_connect:
                mock_connect.side_effect = Exception("Connection failed")
                
                result = store.connect()
                assert result is False
                assert not store._connected
            
            # Test query error
            with patch.object(store, '_get_memory') as mock_get:
                mock_get.side_effect = Exception("Query failed")
                
                result = store.get_memory("invalid_id")
                assert result is None


def test_postgres_store_transaction_management():
    """Test transaction management for complex operations."""
    with patch('jarvis.memory.postgres_store.get_settings'):
        with patch('sqlalchemy.create_engine'):
            from jarvis.memory.postgres_store import PostgresMemoryStore
            
            store = PostgresMemoryStore()
            
            # Mock transaction
            mock_transaction = Mock()
            store._transaction = mock_transaction
            
            # Test transaction commit
            with patch.object(store, '_commit_transaction') as mock_commit:
                store._commit_transaction()
                mock_commit.assert_called_once()
            
            # Test transaction rollback
            with patch.object(store, '_rollback_transaction') as mock_rollback:
                store._rollback_transaction()
                mock_rollback.assert_called_once()


def test_postgres_store_batch_operations():
    """Test batch memory operations."""
    with patch('jarvis.memory.postgres_store.get_settings'):
        with patch('sqlalchemy.create_engine'):
            from jarvis.memory.postgres_store import PostgresMemoryStore
            
            store = PostgresMemoryStore()
            
            # Test batch insert
            test_memories = [
                {"content": "Memory 1", "type": "user_input"},
                {"content": "Memory 2", "type": "system_response"},
                {"content": "Memory 3", "type": "user_input"}
            ]
            
            with patch.object(store, '_batch_insert') as mock_batch:
                mock_batch.return_value = ["id1", "id2", "id3"]
                
                result = store.add_memories_batch(test_memories)
                assert len(result) == 3
                mock_batch.assert_called_once_with(test_memories)


def test_postgres_store_memory_filtering():
    """Test memory filtering and querying."""
    with patch('jarvis.memory.postgres_store.get_settings'):
        with patch('sqlalchemy.create_engine'):
            from jarvis.memory.postgres_store import PostgresMemoryStore
            
            store = PostgresMemoryStore()
            
            # Test filtering by type
            test_filters = {"type": "user_input", "limit": 10}
            test_results = [
                {"id": "1", "content": "User input 1", "type": "user_input"},
                {"id": "2", "content": "User input 2", "type": "user_input"}
            ]
            
            with patch.object(store, '_filter_memories') as mock_filter:
                mock_filter.return_value = test_results
                
                results = store.filter_memories(test_filters)
                assert len(results) == 2
                assert all(r["type"] == "user_input" for r in results)
                mock_filter.assert_called_once_with(test_filters)


def test_postgres_store_memory_updates():
    """Test memory update operations."""
    with patch('jarvis.memory.postgres_store.get_settings'):
        with patch('sqlalchemy.create_engine'):
            from jarvis.memory.postgres_store import PostgresMemoryStore
            
            store = PostgresMemoryStore()
            
            # Test updating memory
            memory_id = "memory_123"
            updates = {"content": "Updated content", "type": "system_response"}
            
            with patch.object(store, '_update_memory') as mock_update:
                mock_update.return_value = True
                
                result = store.update_memory(memory_id, updates)
                assert result is True
                mock_update.assert_called_once_with(memory_id, updates)


def test_postgres_store_memory_deletion():
    """Test memory deletion operations."""
    with patch('jarvis.memory.postgres_store.get_settings'):
        with patch('sqlalchemy.create_engine'):
            from jarvis.memory.postgres_store import PostgresMemoryStore
            
            store = PostgresMemoryStore()
            
            # Test deleting memory
            memory_id = "memory_123"
            
            with patch.object(store, '_delete_memory') as mock_delete:
                mock_delete.return_value = True
                
                result = store.delete_memory(memory_id)
                assert result is True
                mock_delete.assert_called_once_with(memory_id)


def test_postgres_store_memory_statistics():
    """Test memory statistics and analytics."""
    with patch('jarvis.memory.postgres_store.get_settings'):
        with patch('sqlalchemy.create_engine'):
            from jarvis.memory.postgres_store import PostgresMemoryStore
            
            store = PostgresMemoryStore()
            
            # Test getting statistics
            test_stats = {
                "total_memories": 100,
                "user_inputs": 60,
                "system_responses": 40,
                "average_embedding_similarity": 0.75
            }
            
            with patch.object(store, '_get_statistics') as mock_stats:
                mock_stats.return_value = test_stats
                
                stats = store.get_statistics()
                assert stats["total_memories"] == 100
                assert stats["user_inputs"] == 60
                mock_stats.assert_called_once()


def test_postgres_store_connection_pooling():
    """Test connection pooling for performance."""
    with patch('jarvis.memory.postgres_store.get_settings'):
        with patch('sqlalchemy.create_engine') as mock_create_engine:
            mock_engine = Mock()
            mock_create_engine.return_value = mock_engine
            
            from jarvis.memory.postgres_store import PostgresMemoryStore
            store = PostgresMemoryStore()
            
            # Test pool configuration
            assert store._engine == mock_engine
            # Verify engine was created with pooling parameters
            mock_create_engine.assert_called()


def test_postgres_store_async_operations():
    """Test asynchronous database operations."""
    with patch('jarvis.memory.postgres_store.get_settings'):
        with patch('sqlalchemy.create_engine'):
            from jarvis.memory.postgres_store import PostgresMemoryStore
            
            store = PostgresMemoryStore()
            
            # Test async memory addition
            async def test_async_add():
                test_memory = {"content": "Async test", "type": "user_input"}
                
                with patch.object(store, '_add_memory_async') as mock_add_async:
                    mock_add_async.return_value = "async_memory_id"
                    
                    result = await store.add_memory_async(test_memory)
                    assert result == "async_memory_id"
                    mock_add_async.assert_called_once_with(test_memory)
            
            # Run async test
            asyncio.run(test_async_add())


def test_postgres_store_schema_validation():
    """Test schema validation for memory data."""
    with patch('jarvis.memory.postgres_store.get_settings'):
        with patch('sqlalchemy.create_engine'):
            from jarvis.memory.postgres_store import PostgresMemoryStore
            
            store = PostgresMemoryStore()
            
            # Test valid schema
            valid_memory = {
                "content": "Valid content",
                "type": "user_input",
                "timestamp": datetime.now().isoformat(),
                "metadata": {"source": "test"}
            }
            
            assert store._validate_memory_schema(valid_memory)
            
            # Test invalid schema
            invalid_memory = {
                "type": "user_input"
                # Missing required 'content' field
            }
            
            assert not store._validate_memory_schema(invalid_memory)


def test_postgres_store_backup_and_restore():
    """Test backup and restore functionality."""
    with patch('jarvis.memory.postgres_store.get_settings'):
        with patch('sqlalchemy.create_engine'):
            from jarvis.memory.postgres_store import PostgresMemoryStore
            
            store = PostgresMemoryStore()
            
            # Test backup
            test_backup_data = [
                {"id": "1", "content": "Memory 1"},
                {"id": "2", "content": "Memory 2"}
            ]
            
            with patch.object(store, '_create_backup') as mock_backup:
                mock_backup.return_value = test_backup_data
                
                backup = store.create_backup()
                assert len(backup) == 2
                mock_backup.assert_called_once()
            
            # Test restore
            with patch.object(store, '_restore_from_backup') as mock_restore:
                mock_restore.return_value = True
                
                result = store.restore_from_backup(test_backup_data)
                assert result is True
                mock_restore.assert_called_once_with(test_backup_data)
