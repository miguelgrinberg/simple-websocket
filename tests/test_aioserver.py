import asyncio
import unittest
from unittest import mock
import pytest  # noqa: F401

from wsproto.events import Request, CloseConnection, TextMessage, \
    BytesMessage, Ping, Pong
import simple_websocket
from .helpers import make_sync, AsyncMock


class AioSimpleWebSocketServerTestCase(unittest.TestCase):
    async def get_server(self, mock_wsconn, request, events=[],
                         client_subprotocols=None, server_subprotocols=None,
                         **kwargs):
        mock_wsconn().events.side_effect = \
            [iter(ev) for ev in [[
                Request(host='example.com', target='/ws',
                        subprotocols=client_subprotocols or [])]] +
             events + [[CloseConnection(1000, 'bye')]]]
        mock_wsconn().send = lambda x: str(x).encode('utf-8')
        request.headers.update({
            'Host': 'example.com',
            'Connection': 'Upgrade',
            'Upgrade': 'websocket',
            'Sec-Websocket-Key': 'Iv8io/9s+lYFgZWcXczP8Q==',
            'Sec-Websocket-Version': '13',
        })
        return await simple_websocket.AioServer.accept(
            aiohttp=request, subprotocols=server_subprotocols, **kwargs)

    @make_sync
    @mock.patch('simple_websocket.aiows.asyncio.open_connection')
    @mock.patch('simple_websocket.aiows.WSConnection')
    async def test_aiohttp(self, mock_wsconn, mock_open_connection):
        mock_request = mock.MagicMock(headers={})
        rsock = mock.MagicMock(read=AsyncMock(return_value=b'x'))
        wsock = mock.MagicMock()
        mock_open_connection.return_value = (rsock, wsock)
        server = await self.get_server(mock_wsconn, mock_request)
        assert server.rsock == rsock
        assert server.wsock == wsock
        assert server.mode == 'aiohttp'
        assert server.receive_bytes == 4096
        assert server.input_buffer == []
        assert server.event.__class__.__name__ == 'Event'
        mock_wsconn().receive_data.assert_any_call(
            b'GET / HTTP/1.1\r\n'
            b'Host: example.com\r\n'
            b'Connection: Upgrade\r\n'
            b'Upgrade: websocket\r\n'
            b'Sec-Websocket-Key: Iv8io/9s+lYFgZWcXczP8Q==\r\n'
            b'Sec-Websocket-Version: 13\r\n\r\n')
        assert server.is_server

    @make_sync
    async def test_invalid_request(self):
        with pytest.raises(ValueError):
            await simple_websocket.AioServer.accept(aiohttp='foo', asgi='bar')
        with pytest.raises(ValueError):
            await simple_websocket.AioServer.accept(asgi='bar', sock='baz')

    @make_sync
    @mock.patch('simple_websocket.aiows.asyncio.open_connection')
    @mock.patch('simple_websocket.aiows.WSConnection')
    async def test_send(self, mock_wsconn, mock_open_connection):
        mock_request = mock.MagicMock(headers={})
        rsock = mock.MagicMock(read=AsyncMock(return_value=b'x'))
        wsock = mock.MagicMock()
        mock_open_connection.return_value = (rsock, wsock)
        server = await self.get_server(mock_wsconn, mock_request)
        while server.connected:
            await asyncio.sleep(0.01)
        with pytest.raises(simple_websocket.ConnectionClosed):
            await server.send('hello')
        server.connected = True
        await server.send('hello')
        wsock.write.assert_called_with(
            b"TextMessage(data='hello', frame_finished=True, "
            b"message_finished=True)")
        server.connected = True
        await server.send(b'hello')
        wsock.write.assert_called_with(
            b"Message(data=b'hello', frame_finished=True, "
            b"message_finished=True)")

    @make_sync
    @mock.patch('simple_websocket.aiows.asyncio.open_connection')
    @mock.patch('simple_websocket.aiows.WSConnection')
    async def test_receive(self, mock_wsconn, mock_open_connection):
        mock_request = mock.MagicMock(headers={})
        rsock = mock.MagicMock(read=AsyncMock(return_value=b'x'))
        wsock = mock.MagicMock()
        mock_open_connection.return_value = (rsock, wsock)
        server = await self.get_server(mock_wsconn, mock_request, events=[
            [TextMessage('hello')],
            [BytesMessage(b'hello')],
        ])
        while server.connected:
            await asyncio.sleep(0.01)
        server.connected = True
        assert await server.receive() == 'hello'
        assert await server.receive() == b'hello'
        assert await server.receive(timeout=0) is None

    @make_sync
    @mock.patch('simple_websocket.aiows.asyncio.open_connection')
    @mock.patch('simple_websocket.aiows.WSConnection')
    async def test_receive_after_close(self, mock_wsconn,
                                       mock_open_connection):
        mock_request = mock.MagicMock(headers={})
        rsock = mock.MagicMock(read=AsyncMock(return_value=b'x'))
        wsock = mock.MagicMock()
        mock_open_connection.return_value = (rsock, wsock)
        server = await self.get_server(mock_wsconn, mock_request, events=[
            [TextMessage('hello')],
        ])
        while server.connected:
            await asyncio.sleep(0.01)
        assert await server.receive() == 'hello'
        with pytest.raises(simple_websocket.ConnectionClosed):
            await server.receive()

    @make_sync
    @mock.patch('simple_websocket.aiows.asyncio.open_connection')
    @mock.patch('simple_websocket.aiows.WSConnection')
    async def test_receive_split_messages(self, mock_wsconn,
                                          mock_open_connection):
        mock_request = mock.MagicMock(headers={})
        rsock = mock.MagicMock(read=AsyncMock(return_value=b'x'))
        wsock = mock.MagicMock()
        mock_open_connection.return_value = (rsock, wsock)
        server = await self.get_server(mock_wsconn, mock_request, events=[
            [TextMessage('hel', message_finished=False)],
            [TextMessage('lo')],
            [TextMessage('he', message_finished=False)],
            [TextMessage('l', message_finished=False)],
            [TextMessage('lo')],
            [BytesMessage(b'hel', message_finished=False)],
            [BytesMessage(b'lo')],
            [BytesMessage(b'he', message_finished=False)],
            [BytesMessage(b'l', message_finished=False)],
            [BytesMessage(b'lo')],
        ])
        while server.connected:
            await asyncio.sleep(0.01)
        server.connected = True
        assert await server.receive() == 'hello'
        assert await server.receive() == 'hello'
        assert await server.receive() == b'hello'
        assert await server.receive() == b'hello'
        assert await server.receive(timeout=0) is None

    @make_sync
    @mock.patch('simple_websocket.aiows.asyncio.open_connection')
    @mock.patch('simple_websocket.aiows.WSConnection')
    async def test_receive_ping(self, mock_wsconn, mock_open_connection):
        mock_request = mock.MagicMock(headers={})
        rsock = mock.MagicMock(read=AsyncMock(return_value=b'x'))
        wsock = mock.MagicMock()
        mock_open_connection.return_value = (rsock, wsock)
        server = await self.get_server(mock_wsconn, mock_request, events=[
            [Ping(b'hello')],
        ])
        while server.connected:
            await asyncio.sleep(0.01)
        wsock.write.assert_any_call(b"Pong(payload=b'hello')")

    @make_sync
    @mock.patch('simple_websocket.aiows.asyncio.open_connection')
    @mock.patch('simple_websocket.aiows.WSConnection')
    async def test_receive_empty(self, mock_wsconn, mock_open_connection):
        mock_request = mock.MagicMock(headers={})
        rsock = mock.MagicMock(read=AsyncMock(return_value=b'x'))
        wsock = mock.MagicMock()
        mock_open_connection.return_value = (rsock, wsock)
        server = await self.get_server(mock_wsconn, mock_request, events=[
            [TextMessage('hello')],
        ])
        while server.connected:
            await asyncio.sleep(0.01)
        server.connected = True
        assert await server.receive() == 'hello'
        assert await server.receive(timeout=0) is None

    @make_sync
    @mock.patch('simple_websocket.aiows.asyncio.open_connection')
    @mock.patch('simple_websocket.aiows.WSConnection')
    async def test_receive_large(self, mock_wsconn, mock_open_connection):
        mock_request = mock.MagicMock(headers={})
        rsock = mock.MagicMock(read=AsyncMock(return_value=b'x'))
        wsock = mock.MagicMock()
        mock_open_connection.return_value = (rsock, wsock)
        server = await self.get_server(mock_wsconn, mock_request, events=[
            [TextMessage('hello')],
            [TextMessage('hello1')],
        ], max_message_size=5)
        while server.connected:
            await asyncio.sleep(0.01)
        server.connected = True
        assert await server.receive() == 'hello'
        assert await server.receive(timeout=0) is None

    @make_sync
    @mock.patch('simple_websocket.aiows.asyncio.open_connection')
    @mock.patch('simple_websocket.aiows.WSConnection')
    async def test_close(self, mock_wsconn, mock_open_connection):
        mock_request = mock.MagicMock(headers={})
        rsock = mock.MagicMock(read=AsyncMock(return_value=b'x'))
        wsock = mock.MagicMock()
        mock_open_connection.return_value = (rsock, wsock)
        server = await self.get_server(mock_wsconn, mock_request)
        while server.connected:
            await asyncio.sleep(0.01)
        with pytest.raises(simple_websocket.ConnectionClosed) as exc:
            await server.close()
        assert str(exc.value) == 'Connection closed: 1000 bye'
        server.connected = True
        await server.close()
        assert not server.connected
        wsock.write.assert_called_with(
            b'CloseConnection(code=<CloseReason.NORMAL_CLOSURE: 1000>, '
            b'reason=None)')

    @make_sync
    @mock.patch('simple_websocket.aiows.asyncio.open_connection')
    @mock.patch('simple_websocket.aiows.WSConnection')
    @mock.patch('simple_websocket.aiows.time')
    @mock.patch('simple_websocket.aiows.asyncio.wait_for')
    async def test_ping_pong(self, mock_wait_for, mock_time, mock_wsconn,
                             mock_open_connection):
        mock_request = mock.MagicMock(headers={})
        rsock = mock.MagicMock(read=AsyncMock())
        wsock = mock.MagicMock()
        mock_open_connection.return_value = (rsock, wsock)
        server = await self.get_server(mock_wsconn, mock_request, events=[
            [TextMessage('hello')],
            [Pong()],
        ], ping_interval=25)
        mock_wait_for.side_effect = [b'x', b'x', asyncio.TimeoutError,
                                     asyncio.TimeoutError]
        mock_time.side_effect = [0, 1, 25.01, 25.02, 28, 52, 76]
        await server._task()
        assert wsock.write.call_count == 4
        assert wsock.write.call_args_list[1][0][0].startswith(b'Ping')
        assert wsock.write.call_args_list[2][0][0].startswith(b'Ping')
        assert wsock.write.call_args_list[3][0][0].startswith(b'Close')

    @make_sync
    @mock.patch('simple_websocket.aiows.asyncio.open_connection')
    @mock.patch('simple_websocket.aiows.WSConnection')
    async def test_subprotocols(self, mock_wsconn, mock_open_connection):
        mock_request = mock.MagicMock(headers={})
        rsock = mock.MagicMock(read=AsyncMock(return_value=b'x'))
        wsock = mock.MagicMock()
        mock_open_connection.return_value = (rsock, wsock)

        server = await self.get_server(mock_wsconn, mock_request,
                                       client_subprotocols=['foo', 'bar'],
                                       server_subprotocols='bar')
        while server.connected:
            await asyncio.sleep(0.01)
        assert server.subprotocol == 'bar'

        server = await self.get_server(mock_wsconn, mock_request,
                                       client_subprotocols=['foo', 'bar'],
                                       server_subprotocols=['bar'])
        while server.connected:
            await asyncio.sleep(0.01)
        assert server.subprotocol == 'bar'

        server = await self.get_server(mock_wsconn, mock_request,
                                       client_subprotocols=['foo'],
                                       server_subprotocols=['foo', 'bar'])
        while server.connected:
            await asyncio.sleep(0.01)
        assert server.subprotocol == 'foo'

        server = await self.get_server(mock_wsconn, mock_request,
                                       client_subprotocols=['foo'],
                                       server_subprotocols=['bar', 'baz'])
        while server.connected:
            await asyncio.sleep(0.01)
        assert server.subprotocol is None

        server = await self.get_server(mock_wsconn, mock_request,
                                       client_subprotocols=['foo'],
                                       server_subprotocols=None)
        while server.connected:
            await asyncio.sleep(0.01)
        assert server.subprotocol is None
