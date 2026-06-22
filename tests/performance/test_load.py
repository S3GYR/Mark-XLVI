"""Performance and load testing for MARK XLVI components."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
import time
import threading
from typing import Any
from concurrent.futures import ThreadPoolExecutor


def test_memory_store_performance():
    """Test memory store performance under load."""
    with patch('jarvis.memory.json_store.get_settings') as mock_settings:
        mock_settings.return_value.memory_file = "test_memory.json"
        
        from jarvis.memory.json_store import JsonMemoryStore
        
        async def test_memory_performance():
            memory_store = JsonMemoryStore()
            
            # Performance metrics
            start_time = time.time()
            operations = 100
            
            # Test write performance
            for i in range(operations):
                await memory_store.add({
                    "content": f"Test memory entry {i}",
                    "category": "test",
                    "timestamp": time.time()
                })
            
            write_time = time.time() - start_time
            
            # Test read performance
            start_time = time.time()
            for i in range(operations):
                await memory_store.search(f"entry {i}")
            
            read_time = time.time() - start_time
            
            # Performance assertions
            assert write_time < 5.0  # Should complete writes in under 5 seconds
            assert read_time < 2.0   # Should complete reads in under 2 seconds
            
            # Calculate operations per second
            write_ops = operations / write_time
            read_ops = operations / read_time
            
            assert write_ops > 20  # At least 20 writes per second
            assert read_ops > 50   # At least 50 reads per second
        
        asyncio.run(test_memory_performance())


def test_concurrent_command_processing():
    """Test concurrent command processing performance."""
    with patch('jarvis.core.orchestrator.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "gemini/gemini-2.5-flash"
        
        with patch('jarvis.core.orchestrator.get_memory_store') as mock_memory:
            mock_memory_instance = Mock()
            mock_memory.return_value = mock_memory_instance
            
            with patch('jarvis.core.orchestrator.LLMClient') as mock_llm:
                mock_llm_instance = AsyncMock()
                mock_llm_instance.generate_response.return_value = f"Response {{}}"
                mock_llm.return_value = mock_llm_instance
                
                with patch('jarvis.core.orchestrator.ToolRunner') as mock_tool_runner:
                    mock_tool_runner_instance = AsyncMock()
                    mock_tool_runner_instance.run.return_value = "Tool executed"
                    mock_tool_runner.return_value = mock_tool_runner_instance
                    
                    from jarvis.core.orchestrator import AgentOrchestrator
                    orchestrator = AgentOrchestrator()
                    
                    async def test_concurrent_performance():
                        commands = [f"test command {i}" for i in range(50)]
                        
                        start_time = time.time()
                        
                        # Process commands concurrently
                        tasks = [orchestrator.process_command(cmd) for cmd in commands]
                        results = await asyncio.gather(*tasks)
                        
                        processing_time = time.time() - start_time
                        
                        # Performance assertions
                        assert processing_time < 10.0  # Should complete in under 10 seconds
                        assert len(results) == 50       # All commands processed
                        
                        # Calculate commands per second
                        cmd_per_sec = len(commands) / processing_time
                        assert cmd_per_sec > 5  # At least 5 commands per second
                    
                    asyncio.run(test_concurrent_performance())


def test_audio_pipeline_performance():
    """Test audio pipeline performance under load."""
    with patch('jarvis.audio.phone_relay.get_settings'):
        from jarvis.audio.phone_relay import PhoneAudioRelay
        
        async def test_audio_performance():
            callback = Mock()
            relay = PhoneAudioRelay(callback)
            
            # Performance metrics
            start_time = time.time()
            audio_chunks = 100
            chunk_size = 1024
            
            # Test audio processing performance
            for i in range(audio_chunks):
                audio_data = b"x" * chunk_size
                await relay.put(audio_data)
            
            processing_time = time.time() - start_time
            
            # Allow processing to complete
            await asyncio.sleep(0.1)
            
            # Performance assertions
            assert processing_time < 2.0  # Should complete in under 2 seconds
            
            # Calculate chunks per second
            chunks_per_sec = audio_chunks / processing_time
            assert chunks_per_sec > 50  # At least 50 chunks per second
            
            await relay.stop()
        
        asyncio.run(test_audio_performance())


def test_web_server_load():
    """Test web server performance under load."""
    with patch('jarvis.web.server.get_settings') as mock_settings:
        mock_settings.return_value.api_host = "localhost"
        mock_settings.return_value.api_port = 8000
        
        with patch('jarvis.web.server.AgentOrchestrator') as mock_orchestrator:
            mock_orchestrator_instance = AsyncMock()
            mock_orchestrator_instance.process_command.return_value = "Response"
            mock_orchestrator.return_value = mock_orchestrator_instance
            
            from jarvis.web.server import DashboardServer
            
            async def test_web_performance():
                server = DashboardServer()
                
                # Simulate concurrent requests
                requests = 100
                start_time = time.time()
                
                tasks = []
                for i in range(requests):
                    request_data = {"command": f"test command {i}", "user_id": "test_user"}
                    task = asyncio.create_task(server.process_web_command(request_data))
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks)
                
                processing_time = time.time() - start_time
                
                # Performance assertions
                assert processing_time < 15.0  # Should complete in under 15 seconds
                assert len(results) == requests  # All requests processed
                
                # Calculate requests per second
                req_per_sec = requests / processing_time
                assert req_per_sec > 6  # At least 6 requests per second
            
            asyncio.run(test_web_performance())


def test_security_performance():
    """Test security components performance under load."""
    with patch('jarvis.security.permissions.get_settings') as mock_settings:
        mock_settings.return_value.security_level = "high"
        
        from jarvis.security.permissions import PermissionChecker
        from jarvis.security.sandbox import SecureSandbox
        
        def test_security_performance():
            permission_checker = PermissionChecker()
            sandbox = SecureSandbox()
            
            # Test permission checking performance
            start_time = time.time()
            permissions = 1000
            
            for i in range(permissions):
                permission_checker.check_permission(f"command_{i}", "test_action")
            
            permission_time = time.time() - start_time
            
            # Test sandbox execution performance
            start_time = time.time()
            executions = 100
            
            for i in range(executions):
                sandbox.execute_code(f"print('test_{i}')")
            
            sandbox_time = time.time() - start_time
            
            # Performance assertions
            assert permission_time < 1.0  # Should complete in under 1 second
            assert sandbox_time < 5.0    # Should complete in under 5 seconds
            
            # Calculate operations per second
            perm_ops = permissions / permission_time
            sandbox_ops = executions / sandbox_time
            
            assert perm_ops > 1000  # At least 1000 permission checks per second
            assert sandbox_ops > 20  # At least 20 sandbox executions per second
        
        test_security_performance()


def test_memory_usage():
    """Test memory usage under load."""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    with patch('jarvis.memory.json_store.get_settings') as mock_settings:
        mock_settings.return_value.memory_file = "test_memory.json"
        
        from jarvis.memory.json_store import JsonMemoryStore
        
        async def test_memory_usage():
            memory_store = JsonMemoryStore()
            
            # Add large amount of data
            for i in range(1000):
                await memory_store.add({
                    "content": "x" * 1000,  # 1KB per entry
                    "category": "test",
                    "data": list(range(100))  # Additional data
                })
            
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = current_memory - initial_memory
            
            # Memory usage should be reasonable
            assert memory_increase < 100  # Should not increase by more than 100MB
            
            # Test memory cleanup
            await memory_store.cleanup()
            
            # Memory should be freed after cleanup
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_after_cleanup = final_memory - initial_memory
            
            assert memory_after_cleanup < memory_increase * 0.8  # At least 20% memory freed
        
        asyncio.run(test_memory_usage())


def test_thread_safety():
    """Test thread safety of components."""
    with patch('jarvis.memory.json_store.get_settings') as mock_settings:
        mock_settings.return_value.memory_file = "test_memory.json"
        
        from jarvis.memory.json_store import JsonMemoryStore
        
        def test_thread_safety():
            memory_store = JsonMemoryStore()
            results = []
            errors = []
            
            def worker(worker_id):
                try:
                    for i in range(100):
                        memory_store.add({
                            "content": f"Worker {worker_id} entry {i}",
                            "category": "test"
                        })
                        results.append(f"Worker {worker_id} completed {i}")
                except Exception as e:
                    errors.append(f"Worker {worker_id} error: {e}")
            
            # Run multiple threads
            threads = []
            for i in range(10):
                thread = threading.Thread(target=worker, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Verify no errors occurred
            assert len(errors) == 0, f"Thread safety errors: {errors}"
            assert len(results) == 1000  # All operations completed
        
        test_thread_safety()


def test_stress_test():
    """Comprehensive stress test of the system."""
    async def stress_test():
        tasks = []
        
        # Memory store stress
        with patch('jarvis.memory.json_store.get_settings') as mock_settings:
            mock_settings.return_value.memory_file = "stress_test.json"
            
            from jarvis.memory.json_store import JsonMemoryStore
            
            async def memory_stress():
                memory_store = JsonMemoryStore()
                for i in range(500):
                    await memory_store.add({"content": f"Stress test {i}", "category": "stress"})
            
            tasks.append(memory_stress())
        
        # Audio pipeline stress
        with patch('jarvis.audio.phone_relay.get_settings'):
            from jarvis.audio.phone_relay import PhoneAudioRelay
            
            async def audio_stress():
                callback = Mock()
                relay = PhoneAudioRelay(callback)
                for i in range(200):
                    await relay.put(b"stress_test_audio_data")
                await relay.stop()
            
            tasks.append(audio_stress())
        
        # Run all stress tests concurrently
        start_time = time.time()
        await asyncio.gather(*tasks)
        stress_time = time.time() - start_time
        
        # System should handle stress within reasonable time
        assert stress_time < 30.0  # Should complete in under 30 seconds
    
    asyncio.run(stress_test())


def test_resource_cleanup():
    """Test proper resource cleanup under load."""
    async def test_cleanup():
        resources = []
        
        # Create multiple resources
        for i in range(50):
            with patch('jarvis.audio.phone_relay.get_settings'):
                from jarvis.audio.phone_relay import PhoneAudioRelay
                callback = Mock()
                relay = PhoneAudioRelay(callback)
                resources.append(relay)
        
        # Use resources
        for relay in resources:
            await relay.put(b"test_data")
        
        # Cleanup all resources
        cleanup_start = time.time()
        for relay in resources:
            await relay.stop()
        cleanup_time = time.time() - cleanup_start
        
        # Cleanup should be fast
        assert cleanup_time < 5.0  # Should complete in under 5 seconds
        
        # Verify resources are cleaned up
        for relay in resources:
            assert not relay._running
    
    asyncio.run(test_cleanup())
