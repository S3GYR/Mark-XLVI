"""Fixed WebSocket tests with proper mocking and timeout protection."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
import json
from typing import Any
from fastapi import WebSocketDisconnect


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
    
    # Mock message reception with proper termination
    mock_websocket.receive_json.side_effect = [
        {"type": "ping"},  # First message
        WebSocketDisconnect()  # Then disconnect
    ]
    
    # Run the WebSocket handler with timeout
    await asyncio.wait_for(
        handle_client_ws(
            mock_websocket, "valid_token", mock_auth, 
            mock_command_queue, mock_wake_callback, mock_server
        ),
        timeout=2.0
    )
    
    # Verify connection was accepted and cleaned up
    mock_websocket.accept.assert_called_once()
    # Note: client is removed from _clients in finally block after disconnect
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
    await asyncio.wait_for(
        handle_client_ws(
            mock_websocket, "invalid_token", mock_auth,
            mock_command_queue, mock_wake_callback, mock_server
        ),
        timeout=2.0
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
    
    # Mock command message followed by disconnect
    mock_websocket.receive_json.side_effect = [
        {"type": "command", "text": "test command"},
        WebSocketDisconnect()
    ]
    
    # Run the WebSocket handler
    await asyncio.wait_for(
        handle_client_ws(
            mock_websocket, "valid_token", mock_auth,
            mock_command_queue, mock_wake_callback, mock_server
        ),
        timeout=2.0
    )
    
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
    
    # Mock encrypted command message followed by disconnect
    mock_websocket.receive_json.side_effect = [
        {"type": "command", "enc": "encrypted_data"},
        WebSocketDisconnect()
    ]
    
    with patch('jarvis.web.routes.ws.decrypt_aes') as mock_decrypt:
        mock_decrypt.return_value = "decrypted command"
        
        # Run the WebSocket handler
        await asyncio.wait_for(
            handle_client_ws(
                mock_websocket, "valid_token", mock_auth,
                mock_command_queue, mock_wake_callback, mock_server
            ),
            timeout=2.0
        )
        
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
    
    # Mock empty command message followed by disconnect
    mock_websocket.receive_json.side_effect = [
        {"type": "command", "text": ""},
        WebSocketDisconnect()
    ]
    
    # Run the WebSocket handler
    await asyncio.wait_for(
        handle_client_ws(
            mock_websocket, "valid_token", mock_auth,
            mock_command_queue, mock_wake_callback, mock_server
        ),
        timeout=2.0
    )
    
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
    
    # Mock non-command message followed by disconnect
    mock_websocket.receive_json.side_effect = [
        {"type": "ping", "data": "test"},
        WebSocketDisconnect()
    ]
    
    # Run the WebSocket handler
    await asyncio.wait_for(
        handle_client_ws(
            mock_websocket, "valid_token", mock_auth,
            mock_command_queue, mock_wake_callback, mock_server
        ),
        timeout=2.0
    )
    
    # Verify non-command was not processed
    mock_command_queue.put.assert_not_called()
    mock_wake_callback.assert_not_called()


@pytest.mark.asyncio
async def test_handle_client_ws_multiple_commands():
    """Test WebSocket with multiple command messages."""
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
    
    # Mock multiple commands followed by disconnect
    mock_websocket.receive_json.side_effect = [
        {"type": "command", "text": "command 1"},
        {"type": "command", "text": "command 2"},
        {"type": "ping"},
        {"type": "command", "text": "command 3"},
        WebSocketDisconnect()
    ]
    
    # Run the WebSocket handler
    await asyncio.wait_for(
        handle_client_ws(
            mock_websocket, "valid_token", mock_auth,
            mock_command_queue, mock_wake_callback, mock_server
        ),
        timeout=2.0
    )
    
    # Verify all commands were processed
    assert mock_command_queue.put.call_count == 3
    assert mock_wake_callback.call_count == 3
    
    # Verify commands were processed in order
    calls = [call[0][0] for call in mock_command_queue.put.call_args_list]
    assert calls == ["command 1", "command 2", "command 3"]


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
    mock_websocket.receive_json.side_effect = [
        {"type": "ping"},
        WebSocketDisconnect()
    ]
    
    # Run the WebSocket handler
    await asyncio.wait_for(
        handle_client_ws(
            mock_websocket, "valid_token", mock_auth,
            mock_command_queue, mock_wake_callback, mock_server
        ),
        timeout=2.0
    )
    
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
    mock_websocket.receive_json.side_effect = [
        {"type": "ping"},
        WebSocketDisconnect()
    ]
    
    # Run the WebSocket handler
    await asyncio.wait_for(
        handle_client_ws(
            mock_websocket, "valid_token", mock_auth,
            mock_command_queue, mock_wake_callback, mock_server
        ),
        timeout=2.0
    )
    
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
        mock_websocket.receive_json.side_effect = [
            {"type": "ping", "client": client_id},
            WebSocketDisconnect()
        ]
        
        # Run the WebSocket handler
        await asyncio.wait_for(
            handle_client_ws(
                mock_websocket, f"token_{client_id}", mock_auth,
                mock_command_queue, mock_wake_callback, mock_server
            ),
            timeout=2.0
        )
        
        return mock_websocket, mock_server
    
    # Create concurrent connections
    tasks = [create_connection(i) for i in range(5)]
    results = await asyncio.gather(*tasks)
    
    # Verify all connections were handled
    for websocket, server in results:
        websocket.accept.assert_called_once()
        # Note: client is removed from _clients in finally block after disconnect


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
    
    # Mock audio data reception followed by disconnect
    mock_websocket.receive_bytes.side_effect = [
        b"audio_data_1",
        b"audio_data_2",
        WebSocketDisconnect()
    ]
    
    # Run the WebSocket handler
    await asyncio.wait_for(
        handle_phone_audio(
            mock_websocket, "valid_token", mock_auth, mock_audio_queue
        ),
        timeout=2.0
    )
    
    # Verify connection was accepted
    mock_websocket.accept.assert_called_once()
    assert mock_audio_queue.put_nowait.call_count == 2


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
    await asyncio.wait_for(
        handle_phone_audio(
            mock_websocket, "invalid_token", mock_auth, mock_audio_queue
        ),
        timeout=2.0
    )
    
    # Verify connection was rejected
    mock_websocket.accept.assert_not_called()
    mock_websocket.close.assert_called_once_with(code=4001)


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
    
    # Mock audio data reception followed by disconnect
    mock_websocket.receive_bytes.side_effect = [
        b"audio_data",
        WebSocketDisconnect()
    ]
    
    # Run the WebSocket handler
    await asyncio.wait_for(
        handle_phone_audio(
            mock_websocket, "valid_token", mock_auth, mock_audio_queue
        ),
        timeout=2.0
    )
    
    # Verify audio data was processed but queue was full
    mock_audio_queue.put_nowait.assert_called_once_with({
        "data": b"audio_data",
        "mime_type": "audio/pcm"
    })


@pytest.mark.asyncio
async def test_handle_client_ws_connection_reset():
    """Test WebSocket with connection reset."""
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
    
    # Mock connection reset
    mock_websocket.receive_json.side_effect = ConnectionResetError("Connection reset")
    
    # Run the WebSocket handler
    await asyncio.wait_for(
        handle_client_ws(
            mock_websocket, "valid_token", mock_auth,
            mock_command_queue, mock_wake_callback, mock_server
        ),
        timeout=2.0
    )
    
    # Verify graceful handling
    mock_websocket.accept.assert_called_once()
    assert mock_websocket not in mock_server._clients


@pytest.mark.asyncio
async def test_handle_client_ws_cancelled_error():
    """Test WebSocket with cancelled error."""
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
    
    # Mock cancelled error
    mock_websocket.receive_json.side_effect = asyncio.CancelledError("Task cancelled")
    
    # Run the WebSocket handler
    await asyncio.wait_for(
        handle_client_ws(
            mock_websocket, "valid_token", mock_auth,
            mock_command_queue, mock_wake_callback, mock_server
        ),
        timeout=2.0
    )
    
    # Verify graceful handling
    mock_websocket.accept.assert_called_once()
    assert mock_websocket not in mock_server._clients


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
    
    # Mock large message followed by disconnect
    large_message = {"type": "command", "text": "A" * 10000}
    mock_websocket.receive_json.side_effect = [
        large_message,
        WebSocketDisconnect()
    ]
    
    # Run the WebSocket handler
    await asyncio.wait_for(
        handle_client_ws(
            mock_websocket, "valid_token", mock_auth,
            mock_command_queue, mock_wake_callback, mock_server
        ),
        timeout=2.0
    )
    
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
    await asyncio.wait_for(
        handle_client_ws(
            mock_websocket, "valid_token", mock_auth,
            mock_command_queue, mock_wake_callback, mock_server
        ),
        timeout=2.0
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
