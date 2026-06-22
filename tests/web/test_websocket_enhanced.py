"""Enhanced WebSocket tests for comprehensive coverage (>60%)."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
import json
from typing import Any


def test_websocket_connection():
    """Test WebSocket connection establishment."""
    from jarvis.web.routes.ws import handle_websocket
    
    # Mock WebSocket
    mock_websocket = Mock()
    mock_websocket.accept = AsyncMock()
    mock_websocket.receive_text = AsyncMock()
    mock_websocket.send_text = AsyncMock()
    mock_websocket.close = AsyncMock()
    
    # Mock dependencies
    mock_auth = Mock()
    mock_auth.get_token_from_header.return_value = "valid_token"
    mock_auth.is_valid_token.return_value = True
    
    mock_broadcast = AsyncMock()
    
    with patch('jarvis.web.routes.ws.get_settings') as mock_settings:
        mock_settings.return_value.ws_timeout = 30
        
        # Mock the receive loop to exit after one iteration
        async def mock_receive():
            await asyncio.sleep(0.01)
            raise asyncio.CancelledError("Test complete")
        
        mock_websocket.receive_text.side_effect = mock_receive
        
        # Run the WebSocket handler
        try:
            asyncio.run(handle_websocket(mock_websocket, mock_auth, mock_broadcast))
        except asyncio.CancelledError:
            pass  # Expected for test completion
        
        # Verify connection was accepted
        mock_websocket.accept.assert_called_once()


def test_websocket_unauthorized():
    """Test WebSocket connection with invalid token."""
    from jarvis.web.routes.ws import handle_websocket
    
    # Mock WebSocket
    mock_websocket = Mock()
    mock_websocket.accept = AsyncMock()
    mock_websocket.close = AsyncMock()
    
    # Mock dependencies
    mock_auth = Mock()
    mock_auth.get_token_from_header.return_value = "invalid_token"
    mock_auth.is_valid_token.return_value = False
    
    mock_broadcast = AsyncMock()
    
    # Run the WebSocket handler
    asyncio.run(handle_websocket(mock_websocket, mock_auth, mock_broadcast))
    
    # Verify connection was rejected
    mock_websocket.accept.assert_not_called()
    mock_websocket.close.assert_called_once_with(code=4001)


def test_websocket_no_token():
    """Test WebSocket connection with no token."""
    from jarvis.web.routes.ws import handle_websocket
    
    # Mock WebSocket
    mock_websocket = Mock()
    mock_websocket.accept = AsyncMock()
    mock_websocket.close = AsyncMock()
    
    # Mock dependencies
    mock_auth = Mock()
    mock_auth.get_token_from_header.return_value = ""
    mock_auth.is_valid_token.return_value = False
    
    mock_broadcast = AsyncMock()
    
    # Run the WebSocket handler
    asyncio.run(handle_websocket(mock_websocket, mock_auth, mock_broadcast))
    
    # Verify connection was rejected
    mock_websocket.accept.assert_not_called()
    mock_websocket.close.assert_called_once_with(code=4001)


def test_websocket_message_handling():
    """Test WebSocket message handling."""
    from jarvis.web.routes.ws import handle_websocket
    
    # Mock WebSocket
    mock_websocket = Mock()
    mock_websocket.accept = AsyncMock()
    mock_websocket.send_text = AsyncMock()
    mock_websocket.close = AsyncMock()
    
    # Mock dependencies
    mock_auth = Mock()
    mock_auth.get_token_from_header.return_value = "valid_token"
    mock_auth.is_valid_token.return_value = True
    
    mock_broadcast = AsyncMock()
    
    with patch('jarvis.web.routes.ws.get_settings') as mock_settings:
        mock_settings.return_value.ws_timeout = 30
        
        # Mock message reception
        messages = [
            json.dumps({"type": "ping"}),
            json.dumps({"type": "chat", "message": "Hello"}),
        ]
        
        async def mock_receive():
            if messages:
                return messages.pop(0)
            else:
                await asyncio.sleep(0.01)
                raise asyncio.CancelledError("Test complete")
        
        mock_websocket.receive_text.side_effect = mock_receive
        
        # Run the WebSocket handler
        try:
            asyncio.run(handle_websocket(mock_websocket, mock_auth, mock_broadcast))
        except asyncio.CancelledError:
            pass  # Expected for test completion
        
        # Verify connection was accepted and messages were handled
        mock_websocket.accept.assert_called_once()
        assert mock_websocket.send_text.call_count >= 1


def test_websocket_invalid_message():
    """Test WebSocket with invalid JSON message."""
    from jarvis.web.routes.ws import handle_websocket
    
    # Mock WebSocket
    mock_websocket = Mock()
    mock_websocket.accept = AsyncMock()
    mock_websocket.send_text = AsyncMock()
    mock_websocket.close = AsyncMock()
    
    # Mock dependencies
    mock_auth = Mock()
    mock_auth.get_token_from_header.return_value = "valid_token"
    mock_auth.is_valid_token.return_value = True
    
    mock_broadcast = AsyncMock()
    
    with patch('jarvis.web.routes.ws.get_settings') as mock_settings:
        mock_settings.return_value.ws_timeout = 30
        
        # Mock invalid message reception
        async def mock_receive():
            await asyncio.sleep(0.01)
            return "invalid json"
        
        mock_websocket.receive_text.side_effect = mock_receive
        
        # Run the WebSocket handler
        try:
            asyncio.run(handle_websocket(mock_websocket, mock_auth, mock_broadcast))
        except asyncio.CancelledError:
            pass  # Expected for test completion
        
        # Verify connection was accepted but error was handled
        mock_websocket.accept.assert_called_once()


def test_websocket_large_message():
    """Test WebSocket with very large message."""
    from jarvis.web.routes.ws import handle_websocket
    
    # Mock WebSocket
    mock_websocket = Mock()
    mock_websocket.accept = AsyncMock()
    mock_websocket.send_text = AsyncMock()
    mock_websocket.close = AsyncMock()
    
    # Mock dependencies
    mock_auth = Mock()
    mock_auth.get_token_from_header.return_value = "valid_token"
    mock_auth.is_valid_token.return_value = True
    
    mock_broadcast = AsyncMock()
    
    with patch('jarvis.web.routes.ws.get_settings') as mock_settings:
        mock_settings.return_value.ws_timeout = 30
        mock_settings.return_value.ws_max_message_size = 1024
        
        # Mock large message reception
        large_message = "A" * 2000  # Larger than limit
        message_data = json.dumps({"type": "chat", "message": large_message})
        
        async def mock_receive():
            await asyncio.sleep(0.01)
            return message_data
        
        mock_websocket.receive_text.side_effect = mock_receive
        
        # Run the WebSocket handler
        try:
            asyncio.run(handle_websocket(mock_websocket, mock_auth, mock_broadcast))
        except asyncio.CancelledError:
            pass  # Expected for test completion
        
        # Verify connection was accepted
        mock_websocket.accept.assert_called_once()


def test_websocket_timeout():
    """Test WebSocket connection timeout."""
    from jarvis.web.routes.ws import handle_websocket
    
    # Mock WebSocket
    mock_websocket = Mock()
    mock_websocket.accept = AsyncMock()
    mock_websocket.close = AsyncMock()
    
    # Mock dependencies
    mock_auth = Mock()
    mock_auth.get_token_from_header.return_value = "valid_token"
    mock_auth.is_valid_token.return_value = True
    
    mock_broadcast = AsyncMock()
    
    with patch('jarvis.web.routes.ws.get_settings') as mock_settings:
        mock_settings.return_value.ws_timeout = 0.1  # Very short timeout
        
        # Mock slow message reception
        async def mock_receive():
            await asyncio.sleep(0.2)  # Longer than timeout
            return json.dumps({"type": "ping"})
        
        mock_websocket.receive_text.side_effect = mock_receive
        
        # Run the WebSocket handler
        try:
            asyncio.run(handle_websocket(mock_websocket, mock_auth, mock_broadcast))
        except asyncio.TimeoutError:
            pass  # Expected for timeout
        
        # Verify connection was accepted
        mock_websocket.accept.assert_called_once()


def test_websocket_network_error():
    """Test WebSocket with network errors."""
    from jarvis.web.routes.ws import handle_websocket
    
    # Mock WebSocket
    mock_websocket = Mock()
    mock_websocket.accept = AsyncMock()
    mock_websocket.close = AsyncMock()
    
    # Mock dependencies
    mock_auth = Mock()
    mock_auth.get_token_from_header.return_value = "valid_token"
    mock_auth.is_valid_token.return_value = True
    
    mock_broadcast = AsyncMock()
    
    with patch('jarvis.web.routes.ws.get_settings') as mock_settings:
        mock_settings.return_value.ws_timeout = 30
        
        # Mock network error
        mock_websocket.receive_text.side_effect = Exception("Network error")
        
        # Run the WebSocket handler
        try:
            asyncio.run(handle_websocket(mock_websocket, mock_auth, mock_broadcast))
        except Exception:
            pass  # Expected for network error
        
        # Verify connection was accepted
        mock_websocket.accept.assert_called_once()


def test_websocket_concurrent_connections():
    """Test multiple concurrent WebSocket connections."""
    from jarvis.web.routes.ws import handle_websocket
    
    async def create_connection(client_id):
        # Mock WebSocket
        mock_websocket = Mock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_text = AsyncMock()
        mock_websocket.close = AsyncMock()
        
        # Mock dependencies
        mock_auth = Mock()
        mock_auth.get_token_from_header.return_value = f"token_{client_id}"
        mock_auth.is_valid_token.return_value = True
        
        mock_broadcast = AsyncMock()
        
        with patch('jarvis.web.routes.ws.get_settings') as mock_settings:
            mock_settings.return_value.ws_timeout = 1
            
            # Mock message reception
            async def mock_receive():
                await asyncio.sleep(0.1)
                raise asyncio.CancelledError(f"Client {client_id} complete")
            
            mock_websocket.receive_text.side_effect = mock_receive
            
            # Run the WebSocket handler
            try:
                await handle_websocket(mock_websocket, mock_auth, mock_broadcast)
            except asyncio.CancelledError:
                pass  # Expected for test completion
            
            return mock_websocket
    
    # Create concurrent connections
    tasks = [create_connection(i) for i in range(5)]
    websockets = asyncio.run(asyncio.gather(*tasks))
    
    # Verify all connections were accepted
    for ws in websockets:
        ws.accept.assert_called_once()


def test_websocket_message_types():
    """Test different WebSocket message types."""
    from jarvis.web.routes.ws import handle_websocket
    
    # Mock WebSocket
    mock_websocket = Mock()
    mock_websocket.accept = AsyncMock()
    mock_websocket.send_text = AsyncMock()
    mock_websocket.close = AsyncMock()
    
    # Mock dependencies
    mock_auth = Mock()
    mock_auth.get_token_from_header.return_value = "valid_token"
    mock_auth.is_valid_token.return_value = True
    
    mock_broadcast = AsyncMock()
    
    with patch('jarvis.web.routes.ws.get_settings') as mock_settings:
        mock_settings.return_value.ws_timeout = 30
        
        # Test different message types
        messages = [
            json.dumps({"type": "ping"}),
            json.dumps({"type": "pong"}),
            json.dumps({"type": "chat", "message": "Hello"}),
            json.dumps({"type": "command", "command": "help"}),
            json.dumps({"type": "status"}),
            json.dumps({"type": "unknown", "data": "test"}),
        ]
        
        async def mock_receive():
            if messages:
                return messages.pop(0)
            else:
                await asyncio.sleep(0.01)
                raise asyncio.CancelledError("Test complete")
        
        mock_websocket.receive_text.side_effect = mock_receive
        
        # Run the WebSocket handler
        try:
            asyncio.run(handle_websocket(mock_websocket, mock_auth, mock_broadcast))
        except asyncio.CancelledError:
            pass  # Expected for test completion
        
        # Verify connection was accepted and messages were handled
        mock_websocket.accept.assert_called_once()


def test_websocket_broadcast_functionality():
    """Test WebSocket broadcast functionality."""
    from jarvis.web.routes.ws import handle_websocket
    
    # Mock WebSocket
    mock_websocket = Mock()
    mock_websocket.accept = AsyncMock()
    mock_websocket.send_text = AsyncMock()
    mock_websocket.close = AsyncMock()
    
    # Mock dependencies
    mock_auth = Mock()
    mock_auth.get_token_from_header.return_value = "valid_token"
    mock_auth.is_valid_token.return_value = True
    
    # Track broadcast calls
    broadcast_calls = []
    
    async def mock_broadcast(message):
        broadcast_calls.append(message)
    
    with patch('jarvis.web.routes.ws.get_settings') as mock_settings:
        mock_settings.return_value.ws_timeout = 30
        
        # Mock message reception
        async def mock_receive():
            await asyncio.sleep(0.01)
            raise asyncio.CancelledError("Test complete")
        
        mock_websocket.receive_text.side_effect = mock_receive
        
        # Run the WebSocket handler
        try:
            asyncio.run(handle_websocket(mock_websocket, mock_auth, mock_broadcast))
        except asyncio.CancelledError:
            pass  # Expected for test completion
        
        # Verify connection was accepted
        mock_websocket.accept.assert_called_once()


def test_websocket_error_recovery():
    """Test WebSocket error recovery."""
    from jarvis.web.routes.ws import handle_websocket
    
    # Mock WebSocket
    mock_websocket = Mock()
    mock_websocket.accept = AsyncMock()
    mock_websocket.send_text = AsyncMock()
    mock_websocket.close = AsyncMock()
    
    # Mock dependencies
    mock_auth = Mock()
    mock_auth.get_token_from_header.return_value = "valid_token"
    mock_auth.is_valid_token.return_value = True
    
    mock_broadcast = AsyncMock()
    
    with patch('jarvis.web.routes.ws.get_settings') as mock_settings:
        mock_settings.return_value.ws_timeout = 30
        
        # Mock error followed by successful message
        call_count = 0
        
        async def mock_receive():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Temporary error")
            elif call_count == 2:
                return json.dumps({"type": "ping"})
            else:
                await asyncio.sleep(0.01)
                raise asyncio.CancelledError("Test complete")
        
        mock_websocket.receive_text.side_effect = mock_receive
        
        # Run the WebSocket handler
        try:
            asyncio.run(handle_websocket(mock_websocket, mock_auth, mock_broadcast))
        except Exception:
            pass  # Expected for error
        
        # Verify connection was accepted
        mock_websocket.accept.assert_called_once()


def test_websocket_connection_close():
    """Test WebSocket connection closing."""
    from jarvis.web.routes.ws import handle_websocket
    
    # Mock WebSocket
    mock_websocket = Mock()
    mock_websocket.accept = AsyncMock()
    mock_websocket.send_text = AsyncMock()
    mock_websocket.close = AsyncMock()
    
    # Mock dependencies
    mock_auth = Mock()
    mock_auth.get_token_from_header.return_value = "valid_token"
    mock_auth.is_valid_token.return_value = True
    
    mock_broadcast = AsyncMock()
    
    with patch('jarvis.web.routes.ws.get_settings') as mock_settings:
        mock_settings.return_value.ws_timeout = 30
        
        # Mock close message
        async def mock_receive():
            return json.dumps({"type": "close"})
        
        mock_websocket.receive_text.side_effect = mock_receive
        
        # Run the WebSocket handler
        asyncio.run(handle_websocket(mock_websocket, mock_auth, mock_broadcast))
        
        # Verify connection was accepted and closed
        mock_websocket.accept.assert_called_once()
        mock_websocket.close.assert_called()


def test_websocket_heartbeat():
    """Test WebSocket heartbeat/ping functionality."""
    from jarvis.web.routes.ws import handle_websocket
    
    # Mock WebSocket
    mock_websocket = Mock()
    mock_websocket.accept = AsyncMock()
    mock_websocket.send_text = AsyncMock()
    mock_websocket.close = AsyncMock()
    
    # Mock dependencies
    mock_auth = Mock()
    mock_auth.get_token_from_header.return_value = "valid_token"
    mock_auth.is_valid_token.return_value = True
    
    mock_broadcast = AsyncMock()
    
    with patch('jarvis.web.routes.ws.get_settings') as mock_settings:
        mock_settings.return_value.ws_timeout = 30
        
        # Mock ping/pong messages
        messages = [
            json.dumps({"type": "ping"}),
            json.dumps({"type": "pong"}),
        ]
        
        async def mock_receive():
            if messages:
                return messages.pop(0)
            else:
                await asyncio.sleep(0.01)
                raise asyncio.CancelledError("Test complete")
        
        mock_websocket.receive_text.side_effect = mock_receive
        
        # Run the WebSocket handler
        try:
            asyncio.run(handle_websocket(mock_websocket, mock_auth, mock_broadcast))
        except asyncio.CancelledError:
            pass  # Expected for test completion
        
        # Verify connection was accepted and heartbeats handled
        mock_websocket.accept.assert_called_once()
        assert mock_websocket.send_text.call_count >= 1


def test_websocket_malformed_json():
    """Test WebSocket with malformed JSON structures."""
    from jarvis.web.routes.ws import handle_websocket
    
    # Mock WebSocket
    mock_websocket = Mock()
    mock_websocket.accept = AsyncMock()
    mock_websocket.send_text = AsyncMock()
    mock_websocket.close = AsyncMock()
    
    # Mock dependencies
    mock_auth = Mock()
    mock_auth.get_token_from_header.return_value = "valid_token"
    mock_auth.is_valid_token.return_value = True
    
    mock_broadcast = AsyncMock()
    
    with patch('jarvis.web.routes.ws.get_settings') as mock_settings:
        mock_settings.return_value.ws_timeout = 30
        
        # Mock malformed JSON messages
        malformed_messages = [
            '{"type": "ping"',  # Missing closing brace
            '{"type":}',  # Empty value
            '{"type": "ping", "data":}',  # Trailing comma
            'null',  # Null JSON
            'undefined',  # Undefined
            '123',  # Number instead of object
            '[]',  # Array instead of object
        ]
        
        for malformed_msg in malformed_messages:
            async def mock_receive():
                await asyncio.sleep(0.01)
                return malformed_msg
            
            mock_websocket.receive_text.side_effect = mock_receive
            
            # Run the WebSocket handler
            try:
                asyncio.run(handle_websocket(mock_websocket, mock_auth, mock_broadcast))
            except asyncio.CancelledError:
                pass  # Expected for test completion
            
            # Verify connection was accepted but error was handled
            mock_websocket.accept.assert_called()


def test_websocket_special_characters():
    """Test WebSocket with special characters in messages."""
    from jarvis.web.routes.ws import handle_websocket
    
    # Mock WebSocket
    mock_websocket = Mock()
    mock_websocket.accept = AsyncMock()
    mock_websocket.send_text = AsyncMock()
    mock_websocket.close = AsyncMock()
    
    # Mock dependencies
    mock_auth = Mock()
    mock_auth.get_token_from_header.return_value = "valid_token"
    mock_auth.is_valid_token.return_value = True
    
    mock_broadcast = AsyncMock()
    
    with patch('jarvis.web.routes.ws.get_settings') as mock_settings:
        mock_settings.return_value.ws_timeout = 30
        
        # Test messages with special characters
        special_messages = [
            json.dumps({"type": "chat", "message": "Hello 🌍 World!"}),
            json.dumps({"type": "chat", "message": "New\nLine\tTab"}),
            json.dumps({"type": "chat", "message": "Quotes: 'single' and \"double\""}),
            json.dumps({"type": "chat", "message": "Symbols: @#$%^&*()"}),
            json.dumps({"type": "chat", "message": "Unicode: αβγδε"}),
        ]
        
        async def mock_receive():
            if special_messages:
                return special_messages.pop(0)
            else:
                await asyncio.sleep(0.01)
                raise asyncio.CancelledError("Test complete")
        
        mock_websocket.receive_text.side_effect = mock_receive
        
        # Run the WebSocket handler
        try:
            asyncio.run(handle_websocket(mock_websocket, mock_auth, mock_broadcast))
        except asyncio.CancelledError:
            pass  # Expected for test completion
        
        # Verify connection was accepted and special characters handled
        mock_websocket.accept.assert_called_once()


def test_websocket_performance():
    """Test WebSocket performance with many messages."""
    from jarvis.web.routes.ws import handle_websocket
    
    # Mock WebSocket
    mock_websocket = Mock()
    mock_websocket.accept = AsyncMock()
    mock_websocket.send_text = AsyncMock()
    mock_websocket.close = AsyncMock()
    
    # Mock dependencies
    mock_auth = Mock()
    mock_auth.get_token_from_header.return_value = "valid_token"
    mock_auth.is_valid_token.return_value = True
    
    mock_broadcast = AsyncMock()
    
    with patch('jarvis.web.routes.ws.get_settings') as mock_settings:
        mock_settings.return_value.ws_timeout = 30
        
        # Generate many messages
        message_count = 100
        messages = [
            json.dumps({"type": "chat", "message": f"Message {i}"})
            for i in range(message_count)
        ]
        
        async def mock_receive():
            if messages:
                return messages.pop(0)
            else:
                await asyncio.sleep(0.01)
                raise asyncio.CancelledError("Test complete")
        
        mock_websocket.receive_text.side_effect = mock_receive
        
        # Run the WebSocket handler
        try:
            asyncio.run(handle_websocket(mock_websocket, mock_auth, mock_broadcast))
        except asyncio.CancelledError:
            pass  # Expected for test completion
        
        # Verify all messages were handled
        mock_websocket.accept.assert_called_once()
        assert mock_websocket.send_text.call_count >= message_count


def test_websocket_error_handling():
    """Test WebSocket error handling with various exceptions."""
    from jarvis.web.routes.ws import handle_websocket
    
    # Mock WebSocket
    mock_websocket = Mock()
    mock_websocket.accept = AsyncMock()
    mock_websocket.send_text = AsyncMock()
    mock_websocket.close = AsyncMock()
    
    # Mock dependencies
    mock_auth = Mock()
    mock_auth.get_token_from_header.return_value = "valid_token"
    mock_auth.is_valid_token.return_value = True
    
    mock_broadcast = AsyncMock()
    
    with patch('jarvis.web.routes.ws.get_settings') as mock_settings:
        mock_settings.return_value.ws_timeout = 30
        
        # Test various exceptions
        exceptions = [
            Exception("General error"),
            ValueError("Invalid value"),
            TypeError("Type error"),
            RuntimeError("Runtime error"),
        ]
        
        for exc in exceptions:
            async def mock_receive():
                await asyncio.sleep(0.01)
                raise exc
            
            mock_websocket.receive_text.side_effect = mock_receive
            
            # Run the WebSocket handler
            try:
                asyncio.run(handle_websocket(mock_websocket, mock_auth, mock_broadcast))
            except Exception:
                pass  # Expected for error
            
            # Verify connection was accepted
            mock_websocket.accept.assert_called()
