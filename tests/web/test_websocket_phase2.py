"""Phase 2 WebSocket tests for comprehensive coverage (>70%)."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
import json
from typing import Any


@pytest.mark.asyncio
async def test_handle_client_ws_valid_connection():
    """Test valid WebSocket connection and basic flow."""
    from jarvis.web.routes.ws import handle_client_ws
    
    # Mock WebSocket
    mock_websocket = Mock()
    mock_websocket.accept = AsyncMock()
    mock_websocket.receive_json = AsyncMock()
    mock_websocket.send_json = AsyncMock()
    mock_websocket.close = AsyncMock()
    
    # Mock dependencies
    mock_auth = Mock()
    mock_auth.is_valid_token.return_value = True
    mock_auth.get_aes_key.return_value = b"test_aes_key_32_bytes_long"
    
    mock_command_queue = AsyncMock()
    mock_wake_callback = Mock()
    mock_server = Mock()
    mock_server._clients = set()
    mock_server._history = [{"type": "history", "data": "test"}]
    
    # Mock message reception
    async def mock_receive():
        await asyncio.sleep(0.01)
        raise asyncio.CancelledError("Test complete")
    
    mock_websocket.receive_json.side_effect = mock_receive
    
    # Run the WebSocket handler
    try:
        await handle_client_ws(
            mock_websocket, "valid_token", mock_auth, 
            mock_command_queue, mock_wake_callback, mock_server
        )
    except asyncio.CancelledError:
        pass  # Expected for test completion
    
    # Verify connection was accepted
    mock_websocket.accept.assert_called_once()
    assert mock_websocket in mock_server._clients
    mock_websocket.send_json.assert_called_once()


@pytest.mark.asyncio
async def test_handle_client_ws_invalid_token():
    """Test WebSocket connection with invalid token."""
    from jarvis.web.routes.ws import handle_client_ws
    
    # Mock WebSocket
    mock_websocket = Mock()
    mock_websocket.close = AsyncMock()
    
    # Mock dependencies
    mock_auth = Mock()
    mock_auth.is_valid_token.return_value = False
    
    mock_command_queue = AsyncMock()
    mock_wake_callback = Mock()
    mock_server = Mock()
    
    # Run the WebSocket handler
    await handle_client_ws(
        mock_websocket, "invalid_token", mock_auth,
        mock_command_queue, mock_wake_callback, mock_server
    )
    
    # Verify connection was rejected
    mock_websocket.accept.assert_not_called()
    mock_websocket.close.assert_called_once_with(code=4001)


@pytest.mark.asyncio
async def test_handle_client_ws_command_message():
    """Test WebSocket command message handling."""
    from jarvis.web.routes.ws import handle_client_ws
    
    # Mock WebSocket
    mock_websocket = Mock()
    mock_websocket.accept = AsyncMock()
    mock_websocket.receive_json = AsyncMock()
    mock_websocket.send_json = AsyncMock()
    
    # Mock dependencies
    mock_auth = Mock()
    mock_auth.is_valid_token.return_value = True
    mock_auth.get_aes_key.return_value = None  # No encryption
    
    mock_command_queue = AsyncMock()
    mock_wake_callback = Mock()
    mock_server = Mock()
    mock_server._clients = set()
    mock_server._history = []
    
    # Mock command message
    command_message = {"type": "command", "text": "test command"}
    
    async def mock_receive():
        return command_message
    
    mock_websocket.receive_json.side_effect = mock_receive
    
    # Run the WebSocket handler
    try:
        await asyncio.wait_for(
            handle_client_ws(
                mock_websocket, "valid_token", mock_auth,
                mock_command_queue, mock_wake_callback, mock_server
            ),
            timeout=0.1
        )
    except asyncio.TimeoutError:
        pass  # Expected for test completion
    
    # Verify command was processed
    mock_command_queue.put.assert_called_once_with("test command")
    mock_wake_callback.assert_called_once()


@pytest.mark.asyncio
async def test_handle_client_ws_encrypted_command():
    """Test WebSocket encrypted command message handling."""
    from jarvis.web.routes.ws import handle_client_ws
    
    # Mock WebSocket
    mock_websocket = Mock()
    mock_websocket.accept = AsyncMock()
    mock_websocket.receive_json = AsyncMock()
    mock_websocket.send_json = AsyncMock()
    
    # Mock dependencies
    mock_auth = Mock()
    mock_auth.is_valid_token.return_value = True
    mock_auth.get_aes_key.return_value = b"test_aes_key_32_bytes_long"
    
    mock_command_queue = AsyncMock()
    mock_wake_callback = Mock()
    mock_server = Mock()
    mock_server._clients = set()
    mock_server._history = []
    
    # Mock encrypted command message
    encrypted_command = {"type": "command", "enc": "encrypted_data"}
    
    async def mock_receive():
        return encrypted_command
    
    mock_websocket.receive_json.side_effect = mock_receive
    
    with patch('jarvis.web.routes.ws.decrypt_aes') as mock_decrypt:
        mock_decrypt.return_value = "decrypted command"
        
        # Run the WebSocket handler
        try:
            await asyncio.wait_for(
                handle_client_ws(
                    mock_websocket, "valid_token", mock_auth,
                    mock_command_queue, mock_wake_callback, mock_server
                ),
                timeout=0.1
            )
        except asyncio.TimeoutError:
            pass  # Expected for test completion
        
        # Verify decryption was attempted
        mock_decrypt.assert_called_once_with("encrypted_data", b"test_aes_key_32_bytes_long")
        mock_command_queue.put.assert_called_once_with("decrypted command")


@pytest.mark.asyncio
async def test_handle_client_ws_empty_command():
    """Test WebSocket with empty command message."""
    from jarvis.web.routes.ws import handle_client_ws
    
    # Mock WebSocket
    mock_websocket = Mock()
    mock_websocket.accept = AsyncMock()
    mock_websocket.receive_json = AsyncMock()
    mock_websocket.send_json = AsyncMock()
    
    # Mock dependencies
    mock_auth = Mock()
    mock_auth.is_valid_token.return_value = True
    mock_auth.get_aes_key.return_value = None
    
    mock_command_queue = AsyncMock()
    mock_wake_callback = Mock()
    mock_server = Mock()
    mock_server._clients = set()
    mock_server._history = []
    
    # Mock empty command message
    empty_command = {"type": "command", "text": ""}
    
    async def mock_receive():
        return empty_command
    
    mock_websocket.receive_json.side_effect = mock_receive
    
    # Run the WebSocket handler
    try:
        await asyncio.wait_for(
            handle_client_ws(
                mock_websocket, "valid_token", mock_auth,
                mock_command_queue, mock_wake_callback, mock_server
            ),
            timeout=0.1
        )
    except asyncio.TimeoutError:
        pass  # Expected for test completion
    
    # Verify empty command was not processed
    mock_command_queue.put.assert_not_called()
    mock_wake_callback.assert_not_called()


@pytest.mark.asyncio
async def test_handle_client_ws_non_command_message():
    """Test WebSocket with non-command message type."""
    from jarvis.web.routes.ws import handle_client_ws
    
    # Mock WebSocket
    mock_websocket = Mock()
    mock_websocket.accept = AsyncMock()
    mock_websocket.receive_json = AsyncMock()
    mock_websocket.send_json = AsyncMock()
    
    # Mock dependencies
    mock_auth = Mock()
    mock_auth.is_valid_token.return_value = True
    
    mock_command_queue = AsyncMock()
    mock_wake_callback = Mock()
    mock_server = Mock()
    mock_server._clients = set()
    mock_server._history = []
    
    # Mock non-command message
    non_command = {"type": "ping", "data": "test"}
    
    async def mock_receive():
        return non_command
    
    mock_websocket.receive_json.side_effect = mock_receive
    
    # Run the WebSocket handler
    try:
        await asyncio.wait_for(
            handle_client_ws(
                mock_websocket, "valid_token", mock_auth,
                mock_command_queue, mock_wake_callback, mock_server
            ),
            timeout=0.1
        )
    except asyncio.TimeoutError:
        pass  # Expected for test completion
    
    # Verify non-command was not processed
    mock_command_queue.put.assert_not_called()
    mock_wake_callback.assert_not_called()


@pytest.mark.asyncio
async def test_handle_client_ws_websocket_disconnect():
    """Test WebSocket graceful disconnection."""
    from jarvis.web.routes.ws import handle_client_ws
    from fastapi import WebSocketDisconnect
    
    # Mock WebSocket
    mock_websocket = Mock()
    mock_websocket.accept = AsyncMock()
    mock_websocket.receive_json = AsyncMock()
    
    # Mock dependencies
    mock_auth = Mock()
    mock_auth.is_valid_token.return_value = True
    
    mock_command_queue = AsyncMock()
    mock_wake_callback = Mock()
    mock_server = Mock()
    mock_server._clients = set()
    mock_server._history = []
    
    # Mock WebSocketDisconnect
    mock_websocket.receive_json.side_effect = WebSocketDisconnect(code=1000)
    
    # Run the WebSocket handler
    await handle_client_ws(
        mock_websocket, "valid_token", mock_auth,
        mock_command_queue, mock_wake_callback, mock_server
    )
    
    # Verify graceful disconnection
    mock_websocket.accept.assert_called_once()
    assert mock_websocket not in mock_server._clients


@pytest.mark.asyncio
async def test_handle_client_ws_history_broadcast():
    """Test WebSocket history broadcasting on connection."""
    from jarvis.web.routes.ws import handle_client_ws
    
    # Mock WebSocket
    mock_websocket = Mock()
    mock_websocket.accept = AsyncMock()
    mock_websocket.receive_json = AsyncMock()
    mock_websocket.send_json = AsyncMock()
    
    # Mock dependencies
    mock_auth = Mock()
    mock_auth.is_valid_token.return_value = True
    
    mock_command_queue = AsyncMock()
    mock_wake_callback = Mock()
    mock_server = Mock()
    mock_server._clients = set()
    
    # Create history with more than 50 entries
    history = [{"type": "history", "data": f"entry_{i}"} for i in range(60)]
    mock_server._history = history
    
    # Mock message reception
    async def mock_receive():
        await asyncio.sleep(0.01)
        raise asyncio.CancelledError("Test complete")
    
    mock_websocket.receive_json.side_effect = mock_receive
    
    # Run the WebSocket handler
    try:
        await handle_client_ws(
            mock_websocket, "valid_token", mock_auth,
            mock_command_queue, mock_wake_callback, mock_server
        )
    except asyncio.CancelledError:
        pass  # Expected for test completion
    
    # Verify last 50 history entries were sent
    assert mock_websocket.send_json.call_count == 50
    sent_entries = [call[0][0] for call in mock_websocket.send_json.call_args_list]
    expected_entries = history[-50:]
    assert sent_entries == expected_entries


@pytest.mark.asyncio
async def test_handle_client_ws_history_send_error():
    """Test WebSocket history broadcast with send error."""
    from jarvis.web.routes.ws import handle_client_ws
    
    # Mock WebSocket
    mock_websocket = Mock()
    mock_websocket.accept = AsyncMock()
    mock_websocket.receive_json = AsyncMock()
    mock_websocket.send_json = AsyncMock()
    
    # Mock dependencies
    mock_auth = Mock()
    mock_auth.is_valid_token.return_value = True
    
    mock_command_queue = AsyncMock()
    mock_wake_callback = Mock()
    mock_server = Mock()
    mock_server._clients = set()
    
    # Create history
    history = [{"type": "history", "data": f"entry_{i}"} for i in range(5)]
    mock_server._history = history
    
    # Mock send error on third entry
    send_calls = 0
    async def mock_send_json(data):
        nonlocal send_calls
        send_calls += 1
        if send_calls == 3:
            raise Exception("Send error")
    
    mock_websocket.send_json.side_effect = mock_send_json
    
    # Mock message reception
    async def mock_receive():
        await asyncio.sleep(0.01)
        raise asyncio.CancelledError("Test complete")
    
    mock_websocket.receive_json.side_effect = mock_receive
    
    # Run the WebSocket handler
    try:
        await handle_client_ws(
            mock_websocket, "valid_token", mock_auth,
            mock_command_queue, mock_wake_callback, mock_server
        )
    except asyncio.CancelledError:
        pass  # Expected for test completion
    
    # Verify broadcasting stopped on error
    assert mock_websocket.send_json.call_count == 3


@pytest.mark.asyncio
async def test_handle_client_ws_concurrent_connections():
    """Test multiple concurrent WebSocket connections."""
    from jarvis.web.routes.ws import handle_client_ws
    
    async def create_connection(client_id):
        # Mock WebSocket
        mock_websocket = Mock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.receive_json = AsyncMock()
        mock_websocket.send_json = AsyncMock()
        
        # Mock dependencies
        mock_auth = Mock()
        mock_auth.is_valid_token.return_value = True
        
        mock_command_queue = AsyncMock()
        mock_wake_callback = Mock()
        mock_server = Mock()
        mock_server._clients = set()
        mock_server._history = []
        
        # Mock message reception
        async def mock_receive():
            await asyncio.sleep(0.01)
            raise asyncio.CancelledError(f"Client {client_id} complete")
        
        mock_websocket.receive_json.side_effect = mock_receive
        
        # Run the WebSocket handler
        try:
            await handle_client_ws(
                mock_websocket, f"token_{client_id}", mock_auth,
                mock_command_queue, mock_wake_callback, mock_server
            )
        except asyncio.CancelledError:
            pass  # Expected for test completion
        
        return mock_websocket, mock_server
    
    # Create concurrent connections
    tasks = [create_connection(i) for i in range(5)]
    results = await asyncio.gather(*tasks)
    
    # Verify all connections were handled
    for websocket, server in results:
        websocket.accept.assert_called_once()
        assert websocket in server._clients


@pytest.mark.asyncio
async def test_handle_phone_audio_valid_connection():
    """Test phone audio WebSocket connection."""
    from jarvis.web.routes.ws import handle_phone_audio
    
    # Mock WebSocket
    mock_websocket = Mock()
    mock_websocket.accept = AsyncMock()
    mock_websocket.receive_bytes = AsyncMock()
    
    # Mock dependencies
    mock_auth = Mock()
    mock_auth.is_valid_token.return_value = True
    
    mock_audio_queue = AsyncMock()
    
    # Mock audio data reception
    async def mock_receive():
        await asyncio.sleep(0.01)
        raise asyncio.CancelledError("Test complete")
    
    mock_websocket.receive_bytes.side_effect = mock_receive
    
    # Run the WebSocket handler
    try:
        await handle_phone_audio(
            mock_websocket, "valid_token", mock_auth, mock_audio_queue
        )
    except asyncio.CancelledError:
        pass  # Expected for test completion
    
    # Verify connection was accepted
    mock_websocket.accept.assert_called_once()


@pytest.mark.asyncio
async def test_handle_phone_audio_invalid_token():
    """Test phone audio WebSocket with invalid token."""
    from jarvis.web.routes.ws import handle_phone_audio
    
    # Mock WebSocket
    mock_websocket = Mock()
    mock_websocket.close = AsyncMock()
    
    # Mock dependencies
    mock_auth = Mock()
    mock_auth.is_valid_token.return_value = False
    
    mock_audio_queue = AsyncMock()
    
    # Run the WebSocket handler
    await handle_phone_audio(
        mock_websocket, "invalid_token", mock_auth, mock_audio_queue
    )
    
    # Verify connection was rejected
    mock_websocket.accept.assert_not_called()
    mock_websocket.close.assert_called_once_with(code=4001)


@pytest.mark.asyncio
async def test_handle_phone_audio_data_processing():
    """Test phone audio data processing."""
    from jarvis.web.routes.ws import handle_phone_audio
    
    # Mock WebSocket
    mock_websocket = Mock()
    mock_websocket.accept = AsyncMock()
    mock_websocket.receive_bytes = AsyncMock()
    
    # Mock dependencies
    mock_auth = Mock()
    mock_auth.is_valid_token.return_value = True
    
    mock_audio_queue = AsyncMock()
    
    # Mock audio data
    audio_data = b"mock_audio_data"
    
    async def mock_receive():
        return audio_data
    
    mock_websocket.receive_bytes.side_effect = mock_receive
    
    # Run the WebSocket handler
    try:
        await asyncio.wait_for(
            handle_phone_audio(
                mock_websocket, "valid_token", mock_auth, mock_audio_queue
            ),
            timeout=0.1
        )
    except asyncio.TimeoutError:
        pass  # Expected for test completion
    
    # Verify audio data was processed
    mock_audio_queue.put_nowait.assert_called_once_with({
        "data": audio_data,
        "mime_type": "audio/pcm"
    })


@pytest.mark.asyncio
async def test_handle_phone_audio_queue_full():
    """Test phone audio with full queue."""
    from jarvis.web.routes.ws import handle_phone_audio
    
    # Mock WebSocket
    mock_websocket = Mock()
    mock_websocket.accept = AsyncMock()
    mock_websocket.receive_bytes = AsyncMock()
    
    # Mock dependencies
    mock_auth = Mock()
    mock_auth.is_valid_token.return_value = True
    
    mock_audio_queue = AsyncMock()
    mock_audio_queue.put_nowait.side_effect = asyncio.QueueFull()
    
    # Mock audio data
    audio_data = b"mock_audio_data"
    
    async def mock_receive():
        return audio_data
    
    mock_websocket.receive_bytes.side_effect = mock_receive
    
    # Run the WebSocket handler
    try:
        await asyncio.wait_for(
            handle_phone_audio(
                mock_websocket, "valid_token", mock_auth, mock_audio_queue
            ),
            timeout=0.1
        )
    except asyncio.TimeoutError:
        pass  # Expected for test completion
    
    # Verify audio data was processed but queue was full
    mock_audio_queue.put_nowait.assert_called_once()


@pytest.mark.asyncio
async def test_handle_phone_audio_disconnect():
    """Test phone audio WebSocket disconnection."""
    from jarvis.web.routes.ws import handle_phone_audio
    from fastapi import WebSocketDisconnect
    
    # Mock WebSocket
    mock_websocket = Mock()
    mock_websocket.accept = AsyncMock()
    mock_websocket.receive_bytes = AsyncMock()
    
    # Mock dependencies
    mock_auth = Mock()
    mock_auth.is_valid_token.return_value = True
    
    mock_audio_queue = AsyncMock()
    
    # Mock WebSocketDisconnect
    mock_websocket.receive_bytes.side_effect = WebSocketDisconnect(code=1000)
    
    # Run the WebSocket handler
    await handle_phone_audio(
        mock_websocket, "valid_token", mock_auth, mock_audio_queue
    )
    
    # Verify graceful disconnection
    mock_websocket.accept.assert_called_once()


@pytest.mark.asyncio
async def test_handle_client_ws_large_message():
    """Test WebSocket with large message."""
    from jarvis.web.routes.ws import handle_client_ws
    
    # Mock WebSocket
    mock_websocket = Mock()
    mock_websocket.accept = AsyncMock()
    mock_websocket.receive_json = AsyncMock()
    mock_websocket.send_json = AsyncMock()
    
    # Mock dependencies
    mock_auth = Mock()
    mock_auth.is_valid_token.return_value = True
    
    mock_command_queue = AsyncMock()
    mock_wake_callback = Mock()
    mock_server = Mock()
    mock_server._clients = set()
    mock_server._history = []
    
    # Mock large message
    large_message = {"type": "command", "text": "A" * 10000}
    
    async def mock_receive():
        return large_message
    
    mock_websocket.receive_json.side_effect = mock_receive
    
    # Run the WebSocket handler
    try:
        await asyncio.wait_for(
            handle_client_ws(
                mock_websocket, "valid_token", mock_auth,
                mock_command_queue, mock_wake_callback, mock_server
            ),
            timeout=0.1
        )
    except asyncio.TimeoutError:
        pass  # Expected for test completion
    
    # Verify large message was processed
    mock_command_queue.put.assert_called_once_with("A" * 10000)


@pytest.mark.asyncio
async def test_handle_client_ws_invalid_json():
    """Test WebSocket with invalid JSON."""
    from jarvis.web.routes.ws import handle_client_ws
    
    # Mock WebSocket
    mock_websocket = Mock()
    mock_websocket.accept = AsyncMock()
    mock_websocket.receive_json = AsyncMock()
    mock_websocket.send_json = AsyncMock()
    
    # Mock dependencies
    mock_auth = Mock()
    mock_auth.is_valid_token.return_value = True
    
    mock_command_queue = AsyncMock()
    mock_wake_callback = Mock()
    mock_server = Mock()
    mock_server._clients = set()
    mock_server._history = []
    
    # Mock invalid JSON
    mock_websocket.receive_json.side_effect = ValueError("Invalid JSON")
    
    # Run the WebSocket handler
    await handle_client_ws(
        mock_websocket, "valid_token", mock_auth,
        mock_command_queue, mock_wake_callback, mock_server
    )
    
    # Verify connection was handled gracefully
    mock_websocket.accept.assert_called_once()
    assert mock_websocket not in mock_server._clients


@pytest.mark.asyncio
async def test_handle_client_ws_timeout():
    """Test WebSocket with timeout."""
    from jarvis.web.routes.ws import handle_client_ws
    
    # Mock WebSocket
    mock_websocket = Mock()
    mock_websocket.accept = AsyncMock()
    mock_websocket.receive_json = AsyncMock()
    mock_websocket.send_json = AsyncMock()
    
    # Mock dependencies
    mock_auth = Mock()
    mock_auth.is_valid_token.return_value = True
    
    mock_command_queue = AsyncMock()
    mock_wake_callback = Mock()
    mock_server = Mock()
    mock_server._clients = set()
    mock_server._history = []
    
    # Mock timeout
    mock_websocket.receive_json.side_effect = asyncio.TimeoutError()
    
    # Run the WebSocket handler
    await handle_client_ws(
        mock_websocket, "valid_token", mock_auth,
        mock_command_queue, mock_wake_callback, mock_server
    )
    
    # Verify connection was handled gracefully
    mock_websocket.accept.assert_called_once()
    assert mock_websocket not in mock_server._clients


def test_websocket_imports():
    """Test that WebSocket module imports correctly."""
    try:
        from jarvis.web.routes.ws import handle_client_ws, handle_phone_audio
        assert handle_client_ws is not None
        assert handle_phone_audio is not None
    except ImportError:
        pytest.fail("Failed to import WebSocket functions")


def test_websocket_function_signatures():
    """Test WebSocket function signatures."""
    import inspect
    from jarvis.web.routes.ws import handle_client_ws, handle_phone_audio
    
    # Check handle_client_ws signature
    client_sig = inspect.signature(handle_client_ws)
    expected_params = ['websocket', 'token', 'auth', 'command_queue', 'wake_callback', 'server']
    actual_params = list(client_sig.parameters.keys())
    assert actual_params == expected_params
    
    # Check handle_phone_audio signature
    phone_sig = inspect.signature(handle_phone_audio)
    expected_params = ['websocket', 'token', 'auth', 'audio_queue']
    actual_params = list(phone_sig.parameters.keys())
    assert actual_params == expected_params
    
    # Check functions are async
    assert inspect.iscoroutinefunction(handle_client_ws)
    assert inspect.iscoroutinefunction(handle_phone_audio)
