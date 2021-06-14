import unittest
from unittest import mock
import pytest  # noqa: F401

from wsproto.events import CloseConnection, TextMessage, BytesMessage
import simple_websocket


class SimpleWebSocketServerTestCase(unittest.TestCase):
    def get_server(self, mock_wsconn, environ, events=[]):
        mock_wsconn().events.side_effect = events + [[CloseConnection(1000)]]
        mock_wsconn().send = lambda x: str(x).encode('utf-8')
        environ.update({
            'HTTP_HOST': 'example.com',
            'HTTP_CONNECTION': 'Upgrade',
            'HTTP_UPGRADE': 'websocket',
            'HTTP_SEC_WEBSOCKET_KEY': 'Iv8io/9s+lYFgZWcXczP8Q==',
            'HTTP_SEC_WEBSOCKET_VERSION': '13',
        })
        return simple_websocket.Server(environ)

    @mock.patch('simple_websocket.ws.WSConnection')
    def test_werkzeug(self, mock_wsconn):
        mock_socket = mock.MagicMock()
        server = self.get_server(mock_wsconn, {
            'werkzeug.socket': mock_socket,
        })
        assert server.sock == mock_socket
        assert server.receive_bytes == 4096
        assert server.input_buffer == []
        assert server.event.__class__.__name__ == 'Event'
        mock_wsconn().receive_data.assert_called_with(
            b'GET / HTTP/1.1\r\n'
            b'Host: example.com\r\n'
            b'Connection: Upgrade\r\n'
            b'Upgrade: websocket\r\n'
            b'Sec-Websocket-Key: Iv8io/9s+lYFgZWcXczP8Q==\r\n'
            b'Sec-Websocket-Version: 13\r\n\r\n')
        assert not server.connected
        assert server.is_server

    @mock.patch('simple_websocket.ws.WSConnection')
    def test_gunicorn(self, mock_wsconn):
        mock_socket = mock.MagicMock()
        server = self.get_server(mock_wsconn, {
            'gunicorn.socket': mock_socket,
        })
        assert server.sock == mock_socket
        assert server.receive_bytes == 4096
        assert server.input_buffer == []
        assert server.event.__class__.__name__ == 'Event'
        mock_wsconn().receive_data.assert_called_with(
            b'GET / HTTP/1.1\r\n'
            b'Host: example.com\r\n'
            b'Connection: Upgrade\r\n'
            b'Upgrade: websocket\r\n'
            b'Sec-Websocket-Key: Iv8io/9s+lYFgZWcXczP8Q==\r\n'
            b'Sec-Websocket-Version: 13\r\n\r\n')
        assert not server.connected
        assert server.is_server

    def test_no_socket(self):
        with pytest.raises(RuntimeError):
            self.get_server(mock.MagicMock(), {})

    @mock.patch('simple_websocket.ws.WSConnection')
    def test_send(self, mock_wsconn):
        mock_socket = mock.MagicMock()
        server = self.get_server(mock_wsconn, {
            'werkzeug.socket': mock_socket,
        })
        server.connected = False
        with pytest.raises(simple_websocket.ConnectionClosed):
            server.send('hello')
        server.connected = True
        server.send('hello')
        mock_socket.send.assert_called_with(
            b"TextMessage(data='hello', frame_finished=True, "
            b"message_finished=True)")
        server.send(b'hello')
        mock_socket.send.assert_called_with(
            b"Message(data=b'hello', frame_finished=True, "
            b"message_finished=True)")

    @mock.patch('simple_websocket.ws.WSConnection')
    def test_receive(self, mock_wsconn):
        mock_socket = mock.MagicMock()
        server = self.get_server(mock_wsconn, {
            'werkzeug.socket': mock_socket,
        }, events=[
            [TextMessage('hello')],
            [BytesMessage(b'hello')],
        ])
        server.connected = True
        server.event.set()
        assert server.receive() == 'hello'
        server.event.set()
        assert server.receive() == b'hello'
        assert server.receive(timeout=0) is None

    @mock.patch('simple_websocket.ws.WSConnection')
    def test_close(self, mock_wsconn):
        mock_socket = mock.MagicMock()
        server = self.get_server(mock_wsconn, {
            'werkzeug.socket': mock_socket,
        })
        server.connected = False
        with pytest.raises(simple_websocket.ConnectionClosed):
            server.close()
        server.connected = True
        server.close()
        assert not server.connected
        mock_socket.send.assert_called_with(
            b'CloseConnection(code=<CloseReason.NORMAL_CLOSURE: 1000>, '
            b'reason=None)')
