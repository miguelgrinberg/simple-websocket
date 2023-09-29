import asyncio
import unittest
from unittest import mock
import pytest  # noqa: F401

from wsproto.events import AcceptConnection, CloseConnection, TextMessage, \
    BytesMessage, Ping
import simple_websocket
from .helpers import make_sync, AsyncMock


class AioSimpleWebSocketClientTestCase(unittest.TestCase):
    async def get_client(self, mock_wsconn, url, events=[], subprotocols=None,
                         headers=None):
        mock_wsconn().events.side_effect = \
            [iter(ev) for ev in
             [[AcceptConnection()]] + events + [[CloseConnection(1000)]]]
        mock_wsconn().send = lambda x: str(x).encode('utf-8')
        return await simple_websocket.AioClient.connect(
            url, subprotocols=subprotocols, headers=headers)

    @make_sync
    @mock.patch('simple_websocket.aiows.asyncio.open_connection')
    @mock.patch('simple_websocket.aiows.WSConnection')
    async def test_make_client(self, mock_wsconn, mock_open_connection):
        rsock = mock.MagicMock(read=AsyncMock(return_value=b'x'))
        wsock = mock.MagicMock()
        mock_open_connection.return_value = (rsock, wsock)
        client = await self.get_client(mock_wsconn, 'ws://example.com/ws?a=1')
        assert client.rsock == rsock
        assert client.wsock == wsock
        assert client.receive_bytes == 4096
        assert client.input_buffer == []
        assert client.event.__class__.__name__ == 'Event'
        client.wsock.write.assert_called_with(
            b"Request(host='example.com', target='/ws?a=1', extensions=[], "
            b"extra_headers=[], subprotocols=[])")
        assert not client.is_server
        assert client.host == 'example.com'
        assert client.port == 80
        assert client.path == '/ws?a=1'

    @make_sync
    @mock.patch('simple_websocket.aiows.asyncio.open_connection')
    @mock.patch('simple_websocket.aiows.WSConnection')
    async def test_make_client_subprotocol(self, mock_wsconn,
                                           mock_open_connection):
        rsock = mock.MagicMock(read=AsyncMock(return_value=b'x'))
        wsock = mock.MagicMock()
        mock_open_connection.return_value = (rsock, wsock)
        client = await self.get_client(mock_wsconn, 'ws://example.com/ws?a=1',
                                       subprotocols='foo')
        assert client.subprotocols == ['foo']
        client.wsock.write.assert_called_with(
            b"Request(host='example.com', target='/ws?a=1', extensions=[], "
            b"extra_headers=[], subprotocols=['foo'])")

    @make_sync
    @mock.patch('simple_websocket.aiows.asyncio.open_connection')
    @mock.patch('simple_websocket.aiows.WSConnection')
    async def test_make_client_subprotocols(self, mock_wsconn,
                                            mock_open_connection):
        rsock = mock.MagicMock(read=AsyncMock(return_value=b'x'))
        wsock = mock.MagicMock()
        mock_open_connection.return_value = (rsock, wsock)
        client = await self.get_client(mock_wsconn, 'ws://example.com/ws?a=1',
                                       subprotocols=['foo', 'bar'])
        assert client.subprotocols == ['foo', 'bar']
        client.wsock.write.assert_called_with(
            b"Request(host='example.com', target='/ws?a=1', extensions=[], "
            b"extra_headers=[], subprotocols=['foo', 'bar'])")

    @make_sync
    @mock.patch('simple_websocket.aiows.asyncio.open_connection')
    @mock.patch('simple_websocket.aiows.WSConnection')
    async def test_make_client_headers(self, mock_wsconn,
                                       mock_open_connection):
        rsock = mock.MagicMock(read=AsyncMock(return_value=b'x'))
        wsock = mock.MagicMock()
        mock_open_connection.return_value = (rsock, wsock)
        client = await self.get_client(mock_wsconn, 'ws://example.com/ws?a=1',
                                       headers={'Foo': 'Bar'})
        client.wsock.write.assert_called_with(
            b"Request(host='example.com', target='/ws?a=1', extensions=[], "
            b"extra_headers=[('Foo', 'Bar')], subprotocols=[])")

    @make_sync
    @mock.patch('simple_websocket.aiows.asyncio.open_connection')
    @mock.patch('simple_websocket.aiows.WSConnection')
    async def test_make_client_headers2(self, mock_wsconn,
                                        mock_open_connection):
        rsock = mock.MagicMock(read=AsyncMock(return_value=b'x'))
        wsock = mock.MagicMock()
        mock_open_connection.return_value = (rsock, wsock)
        client = await self.get_client(
            mock_wsconn, 'ws://example.com/ws?a=1',
            headers=[('Foo', 'Bar'), ('Foo', 'Baz')])
        client.wsock.write.assert_called_with(
            b"Request(host='example.com', target='/ws?a=1', extensions=[], "
            b"extra_headers=[('Foo', 'Bar'), ('Foo', 'Baz')], "
            b"subprotocols=[])")

    @make_sync
    @mock.patch('simple_websocket.aiows.asyncio.open_connection')
    @mock.patch('simple_websocket.aiows.WSConnection')
    async def test_send(self, mock_wsconn, mock_open_connection):
        rsock = mock.MagicMock(read=AsyncMock(return_value=b'x'))
        wsock = mock.MagicMock()
        mock_open_connection.return_value = (rsock, wsock)
        client = await self.get_client(mock_wsconn, 'ws://example.com/ws')
        while client.connected:
            await asyncio.sleep(0.01)
        with pytest.raises(simple_websocket.ConnectionClosed):
            await client.send('hello')
        client.connected = True
        await client.send('hello')
        wsock.write.assert_called_with(
            b"TextMessage(data='hello', frame_finished=True, "
            b"message_finished=True)")
        client.connected = True
        await client.send(b'hello')
        wsock.write.assert_called_with(
            b"Message(data=b'hello', frame_finished=True, "
            b"message_finished=True)")

    @make_sync
    @mock.patch('simple_websocket.aiows.asyncio.open_connection')
    @mock.patch('simple_websocket.aiows.WSConnection')
    async def test_receive(self, mock_wsconn, mock_open_connection):
        rsock = mock.MagicMock(read=AsyncMock(return_value=b'x'))
        wsock = mock.MagicMock()
        mock_open_connection.return_value = (rsock, wsock)
        client = await self.get_client(
            mock_wsconn, 'ws://example.com/ws', events=[
                [TextMessage('hello')],
                [BytesMessage(b'hello')],
            ])
        while client.connected:
            await asyncio.sleep(0.01)
        client.connected = True
        assert await client.receive() == 'hello'
        assert await client.receive() == b'hello'
        assert await client.receive(timeout=0) is None

    @make_sync
    @mock.patch('simple_websocket.aiows.asyncio.open_connection')
    @mock.patch('simple_websocket.aiows.WSConnection')
    async def test_receive_after_close(self, mock_wsconn,
                                       mock_open_connection):
        rsock = mock.MagicMock(read=AsyncMock(return_value=b'x'))
        wsock = mock.MagicMock()
        mock_open_connection.return_value = (rsock, wsock)
        client = await self.get_client(
            mock_wsconn, 'ws://example.com/ws', events=[
                [TextMessage('hello')],
            ])
        while client.connected:
            await asyncio.sleep(0.01)
        assert await client.receive() == 'hello'
        with pytest.raises(simple_websocket.ConnectionClosed):
            await client.receive()

    @make_sync
    @mock.patch('simple_websocket.aiows.asyncio.open_connection')
    @mock.patch('simple_websocket.aiows.WSConnection')
    async def test_receive_ping(self, mock_wsconn, mock_open_connection):
        rsock = mock.MagicMock(read=AsyncMock(return_value=b'x'))

        wsock = mock.MagicMock()
        mock_open_connection.return_value = (rsock, wsock)
        client = await self.get_client(
            mock_wsconn, 'ws://example.com/ws', events=[
                [Ping(b'hello')],
            ])
        while client.connected:
            await asyncio.sleep(0.01)
        wsock.write.assert_any_call(b"Pong(payload=b'hello')")

    @make_sync
    @mock.patch('simple_websocket.aiows.asyncio.open_connection')
    @mock.patch('simple_websocket.aiows.WSConnection')
    async def test_receive_empty(self, mock_wsconn, mock_open_connection):
        rsock = mock.MagicMock(read=AsyncMock(side_effect=[b'x', b'x', b'']))
        wsock = mock.MagicMock()
        mock_open_connection.return_value = (rsock, wsock)
        client = await self.get_client(
            mock_wsconn, 'ws://example.com/ws', events=[
                [TextMessage('hello')],
            ])
        while client.connected:
            await asyncio.sleep(0.01)
        client.connected = True
        assert await client.receive() == 'hello'
        assert await client.receive(timeout=0) is None

    @make_sync
    @mock.patch('simple_websocket.aiows.asyncio.open_connection')
    @mock.patch('simple_websocket.aiows.WSConnection')
    async def test_close(self, mock_wsconn, mock_open_connection):
        rsock = mock.MagicMock(read=AsyncMock(return_value=b'x'))
        wsock = mock.MagicMock()
        mock_open_connection.return_value = (rsock, wsock)
        client = await self.get_client(
            mock_wsconn, 'ws://example.com/ws')
        while client.connected:
            await asyncio.sleep(0.01)
        with pytest.raises(simple_websocket.ConnectionClosed):
            await client.close()
        client.connected = True
        await client.close()
        assert not client.connected
        wsock.write.assert_called_with(
            b'CloseConnection(code=<CloseReason.NORMAL_CLOSURE: 1000>, '
            b'reason=None)')
