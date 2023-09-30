import time
import unittest
from unittest import mock
import pytest  # noqa: F401

from wsproto.events import AcceptConnection, CloseConnection, TextMessage, \
    BytesMessage, Ping
import simple_websocket


class SimpleWebSocketClientTestCase(unittest.TestCase):
    def get_client(self, mock_wsconn, url, events=[], subprotocols=None,
                   headers=None):
        mock_wsconn().events.side_effect = \
            [iter(ev) for ev in
             [[AcceptConnection()]] + events + [[CloseConnection(1000)]]]
        mock_wsconn().send = lambda x: str(x).encode('utf-8')
        return simple_websocket.Client.connect(url, subprotocols=subprotocols,
                                               headers=headers)

    @mock.patch('simple_websocket.ws.socket.socket')
    @mock.patch('simple_websocket.ws.WSConnection')
    def test_make_client(self, mock_wsconn, mock_socket):
        mock_socket.return_value.recv.return_value = b'x'
        client = self.get_client(mock_wsconn, 'ws://example.com/ws?a=1')
        assert client.sock == mock_socket()
        assert client.receive_bytes == 4096
        assert client.input_buffer == []
        assert client.event.__class__.__name__ == 'Event'
        client.sock.send.assert_called_with(
            b"Request(host='example.com', target='/ws?a=1', extensions=[], "
            b"extra_headers=[], subprotocols=[])")
        assert not client.is_server
        assert client.host == 'example.com'
        assert client.port == 80
        assert client.path == '/ws?a=1'

    @mock.patch('simple_websocket.ws.socket.socket')
    @mock.patch('simple_websocket.ws.WSConnection')
    def test_make_client_subprotocol(self, mock_wsconn, mock_socket):
        mock_socket.return_value.recv.return_value = b'x'
        client = self.get_client(mock_wsconn, 'ws://example.com/ws?a=1',
                                 subprotocols='foo')
        assert client.subprotocols == ['foo']
        client.sock.send.assert_called_with(
            b"Request(host='example.com', target='/ws?a=1', extensions=[], "
            b"extra_headers=[], subprotocols=['foo'])")

    @mock.patch('simple_websocket.ws.socket.socket')
    @mock.patch('simple_websocket.ws.WSConnection')
    def test_make_client_subprotocols(self, mock_wsconn, mock_socket):
        mock_socket.return_value.recv.return_value = b'x'
        client = self.get_client(mock_wsconn, 'ws://example.com/ws?a=1',
                                 subprotocols=['foo', 'bar'])
        assert client.subprotocols == ['foo', 'bar']
        client.sock.send.assert_called_with(
            b"Request(host='example.com', target='/ws?a=1', extensions=[], "
            b"extra_headers=[], subprotocols=['foo', 'bar'])")

    @mock.patch('simple_websocket.ws.socket.socket')
    @mock.patch('simple_websocket.ws.WSConnection')
    def test_make_client_headers(self, mock_wsconn, mock_socket):
        mock_socket.return_value.recv.return_value = b'x'
        client = self.get_client(mock_wsconn, 'ws://example.com/ws?a=1',
                                 headers={'Foo': 'Bar'})
        client.sock.send.assert_called_with(
            b"Request(host='example.com', target='/ws?a=1', extensions=[], "
            b"extra_headers=[('Foo', 'Bar')], subprotocols=[])")

    @mock.patch('simple_websocket.ws.socket.socket')
    @mock.patch('simple_websocket.ws.WSConnection')
    def test_make_client_headers2(self, mock_wsconn, mock_socket):
        mock_socket.return_value.recv.return_value = b'x'
        client = self.get_client(mock_wsconn, 'ws://example.com/ws?a=1',
                                 headers=[('Foo', 'Bar'), ('Foo', 'Baz')])
        client.sock.send.assert_called_with(
            b"Request(host='example.com', target='/ws?a=1', extensions=[], "
            b"extra_headers=[('Foo', 'Bar'), ('Foo', 'Baz')], "
            b"subprotocols=[])")

    @mock.patch('simple_websocket.ws.socket.socket')
    @mock.patch('simple_websocket.ws.WSConnection')
    def test_send(self, mock_wsconn, mock_socket):
        mock_socket.return_value.recv.return_value = b'x'
        client = self.get_client(mock_wsconn, 'ws://example.com/ws')
        while client.connected:
            time.sleep(0.01)
        with pytest.raises(simple_websocket.ConnectionClosed):
            client.send('hello')
        client.connected = True
        client.send('hello')
        mock_socket().send.assert_called_with(
            b"TextMessage(data='hello', frame_finished=True, "
            b"message_finished=True)")
        client.connected = True
        client.send(b'hello')
        mock_socket().send.assert_called_with(
            b"Message(data=b'hello', frame_finished=True, "
            b"message_finished=True)")

    @mock.patch('simple_websocket.ws.socket.socket')
    @mock.patch('simple_websocket.ws.WSConnection')
    def test_receive(self, mock_wsconn, mock_socket):
        mock_socket.return_value.recv.return_value = b'x'
        client = self.get_client(mock_wsconn, 'ws://example.com/ws', events=[
            [TextMessage('hello')],
            [BytesMessage(b'hello')],
        ])
        while client.connected:
            time.sleep(0.01)
        client.connected = True
        assert client.receive() == 'hello'
        assert client.receive() == b'hello'
        assert client.receive(timeout=0) is None

    @mock.patch('simple_websocket.ws.socket.socket')
    @mock.patch('simple_websocket.ws.WSConnection')
    def test_receive_after_close(self, mock_wsconn, mock_socket):
        mock_socket.return_value.recv.return_value = b'x'
        client = self.get_client(mock_wsconn, 'ws://example.com/ws', events=[
            [TextMessage('hello')],
        ])
        while client.connected:
            time.sleep(0.01)
        assert client.receive() == 'hello'
        with pytest.raises(simple_websocket.ConnectionClosed):
            client.receive()

    @mock.patch('simple_websocket.ws.socket.socket')
    @mock.patch('simple_websocket.ws.WSConnection')
    def test_receive_ping(self, mock_wsconn, mock_socket):
        mock_socket.return_value.recv.return_value = b'x'
        client = self.get_client(mock_wsconn, 'ws://example.com/ws', events=[
            [Ping(b'hello')],
        ])
        while client.connected:
            time.sleep(0.01)
        mock_socket().send.assert_any_call(b"Pong(payload=b'hello')")

    @mock.patch('simple_websocket.ws.socket.socket')
    @mock.patch('simple_websocket.ws.WSConnection')
    def test_receive_empty(self, mock_wsconn, mock_socket):
        mock_socket.return_value.recv.side_effect = [b'x', b'x', b'']
        client = self.get_client(mock_wsconn, 'ws://example.com/ws', events=[
            [TextMessage('hello')],
        ])
        while client.connected:
            time.sleep(0.01)
        client.connected = True
        assert client.receive() == 'hello'
        assert client.receive(timeout=0) is None

    @mock.patch('simple_websocket.ws.socket.socket')
    @mock.patch('simple_websocket.ws.WSConnection')
    def test_close(self, mock_wsconn, mock_socket):
        mock_socket.return_value.recv.return_value = b'x'
        client = self.get_client(mock_wsconn, 'ws://example.com/ws')
        while client.connected:
            time.sleep(0.01)
        with pytest.raises(simple_websocket.ConnectionClosed):
            client.close()
        client.connected = True
        client.close()
        assert not client.connected
        mock_socket().send.assert_called_with(
            b'CloseConnection(code=<CloseReason.NORMAL_CLOSURE: 1000>, '
            b'reason=None)')
