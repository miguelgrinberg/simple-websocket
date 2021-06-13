import unittest
from unittest import mock
import pytest  # noqa: F401

from wsproto.events import CloseConnection
import simple_websocket


class SimpleWebSocketServerTestCase(unittest.TestCase):
    def websocket_request(self, environ):
        environ.update({
            'HTTP_HOST': 'example.com',
            'HTTP_CONNECTION': 'Upgrade',
            'HTTP_UPGRADE': 'websocket',
            'HTTP_SEC_WEBSOCKET_KEY': 'Iv8io/9s+lYFgZWcXczP8Q==',
            'HTTP_SEC_WEBSOCKET_VERSION': '13',
        })
        return environ

    @mock.patch('simple_websocket.ws.WSConnection')
    def test_werkzeug(self, mock_wsconn):
        wsconn = mock_wsconn()
        wsconn.events.return_value = [CloseConnection(1000)]
        mock_socket = mock.MagicMock()
        server = simple_websocket.Server(self.websocket_request({
            'werkzeug.socket': mock_socket,
        }))
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
        wsconn = mock_wsconn()
        wsconn.events.return_value = [CloseConnection(1000)]
        mock_socket = mock.MagicMock()
        server = simple_websocket.Server(self.websocket_request({
            'gunicorn.socket': mock_socket,
        }))
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
            simple_websocket.Server({
                'HTTP_HOST': 'example.com',
                'HTTP_CONNECTION': 'Upgrade',
                'HTTP_UPGRADE': 'websocket',
                'HTTP_SEC_WEBSOCKET_KEY': 'Iv8io/9s+lYFgZWcXczP8Q==',
                'HTTP_SEC_WEBSOCKET_VERSION': '13',
            })
