import time
import unittest
from unittest import mock
import pytest  # noqa: F401

from wsproto.events import Request, CloseConnection, TextMessage, \
    BytesMessage, Ping, Pong
import simple_websocket


class SimpleWebSocketServerTestCase(unittest.TestCase):
    def get_server(self, mock_wsconn, environ, events=[],
                   client_subprotocols=None, server_subprotocols=None,
                   **kwargs):
        mock_wsconn().events.side_effect = \
            [iter(ev) for ev in [[
                Request(host='example.com', target='/ws',
                        subprotocols=client_subprotocols or [])]] +
             events + [[CloseConnection(1000, 'bye')]]]
        mock_wsconn().send = lambda x: str(x).encode('utf-8')
        environ.update({
            'HTTP_HOST': 'example.com',
            'HTTP_CONNECTION': 'Upgrade',
            'HTTP_UPGRADE': 'websocket',
            'HTTP_SEC_WEBSOCKET_KEY': 'Iv8io/9s+lYFgZWcXczP8Q==',
            'HTTP_SEC_WEBSOCKET_VERSION': '13',
        })
        return simple_websocket.Server.accept(
            environ, subprotocols=server_subprotocols, **kwargs)

    @mock.patch('simple_websocket.ws.WSConnection')
    def test_werkzeug(self, mock_wsconn):
        mock_socket = mock.MagicMock()
        mock_socket.recv.return_value = b'x'
        server = self.get_server(mock_wsconn, {
            'werkzeug.socket': mock_socket,
        })
        assert server.sock == mock_socket
        assert server.mode == 'werkzeug'
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

    @mock.patch('simple_websocket.ws.WSConnection')
    def test_gunicorn(self, mock_wsconn):
        mock_socket = mock.MagicMock()
        mock_socket.recv.return_value = b'x'
        server = self.get_server(mock_wsconn, {
            'gunicorn.socket': mock_socket,
        })
        assert server.sock == mock_socket
        assert server.mode == 'gunicorn'
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

    def test_no_socket(self):
        with pytest.raises(RuntimeError):
            self.get_server(mock.MagicMock(), {})

    @mock.patch('simple_websocket.ws.WSConnection')
    def test_send(self, mock_wsconn):
        mock_socket = mock.MagicMock()
        mock_socket.recv.return_value = b'x'
        server = self.get_server(mock_wsconn, {
            'werkzeug.socket': mock_socket,
        })
        while server.connected:
            time.sleep(0.01)
        with pytest.raises(simple_websocket.ConnectionClosed):
            server.send('hello')
        server.connected = True
        server.send('hello')
        mock_socket.send.assert_called_with(
            b"TextMessage(data='hello', frame_finished=True, "
            b"message_finished=True)")
        server.connected = True
        server.send(b'hello')
        mock_socket.send.assert_called_with(
            b"Message(data=b'hello', frame_finished=True, "
            b"message_finished=True)")

    @mock.patch('simple_websocket.ws.WSConnection')
    def test_receive(self, mock_wsconn):
        mock_socket = mock.MagicMock()
        mock_socket.recv.return_value = b'x'
        server = self.get_server(mock_wsconn, {
            'werkzeug.socket': mock_socket,
        }, events=[
            [TextMessage('hello')],
            [BytesMessage(b'hello')],
        ])
        while server.connected:
            time.sleep(0.01)
        server.connected = True
        assert server.receive() == 'hello'
        assert server.receive() == b'hello'
        assert server.receive(timeout=0) is None

    @mock.patch('simple_websocket.ws.WSConnection')
    def test_receive_after_close(self, mock_wsconn):
        mock_socket = mock.MagicMock()
        mock_socket.recv.return_value = b'x'
        server = self.get_server(mock_wsconn, {
            'werkzeug.socket': mock_socket,
        }, events=[
            [TextMessage('hello')],
        ])
        while server.connected:
            time.sleep(0.01)
        assert server.receive() == 'hello'
        with pytest.raises(simple_websocket.ConnectionClosed):
            server.receive()

    @mock.patch('simple_websocket.ws.WSConnection')
    def test_receive_split_messages(self, mock_wsconn):
        mock_socket = mock.MagicMock()
        mock_socket.recv.return_value = b'x'
        server = self.get_server(mock_wsconn, {
            'werkzeug.socket': mock_socket,
        }, events=[
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
            time.sleep(0.01)
        server.connected = True
        assert server.receive() == 'hello'
        assert server.receive() == 'hello'
        assert server.receive() == b'hello'
        assert server.receive() == b'hello'
        assert server.receive(timeout=0) is None

    @mock.patch('simple_websocket.ws.WSConnection')
    def test_receive_ping(self, mock_wsconn):
        mock_socket = mock.MagicMock()
        mock_socket.recv.return_value = b'x'
        server = self.get_server(mock_wsconn, {
            'werkzeug.socket': mock_socket,
        }, events=[
            [Ping(b'hello')],
        ])
        while server.connected:
            time.sleep(0.01)
        mock_socket.send.assert_any_call(b"Pong(payload=b'hello')")

    @mock.patch('simple_websocket.ws.WSConnection')
    def test_receive_empty(self, mock_wsconn):
        mock_socket = mock.MagicMock()
        mock_socket.recv.side_effect = [b'x', b'x', b'']
        server = self.get_server(mock_wsconn, {
            'werkzeug.socket': mock_socket,
        }, events=[
            [TextMessage('hello')],
        ])
        while server.connected:
            time.sleep(0.01)
        server.connected = True
        assert server.receive() == 'hello'
        assert server.receive(timeout=0) is None

    @mock.patch('simple_websocket.ws.WSConnection')
    def test_receive_large(self, mock_wsconn):
        mock_socket = mock.MagicMock()
        mock_socket.recv.return_value = b'x'
        server = self.get_server(mock_wsconn, {
            'werkzeug.socket': mock_socket,
        }, events=[
            [TextMessage('hello')],
            [TextMessage('hello1')],
        ], max_message_size=5)
        while server.connected:
            time.sleep(0.01)
        server.connected = True
        assert server.receive() == 'hello'
        assert server.receive(timeout=0) is None

    @mock.patch('simple_websocket.ws.WSConnection')
    def test_close(self, mock_wsconn):
        mock_socket = mock.MagicMock()
        mock_socket.recv.return_value = b'x'
        server = self.get_server(mock_wsconn, {
            'werkzeug.socket': mock_socket,
        })
        while server.connected:
            time.sleep(0.01)
        with pytest.raises(simple_websocket.ConnectionClosed) as exc:
            server.close()
        assert str(exc.value) == 'Connection closed: 1000 bye'
        server.connected = True
        server.close()
        assert not server.connected
        mock_socket.send.assert_called_with(
            b'CloseConnection(code=<CloseReason.NORMAL_CLOSURE: 1000>, '
            b'reason=None)')

    @mock.patch('simple_websocket.ws.WSConnection')
    @mock.patch('simple_websocket.ws.time')
    def test_ping_pong(self, mock_time, mock_wsconn):
        mock_sel = mock.MagicMock()
        mock_sel().select.side_effect = [True, True, False, False]
        mock_time.side_effect = [0, 1, 25.01, 25.02, 28, 52, 76]
        mock_socket = mock.MagicMock()
        mock_socket.recv.side_effect = [b'x', b'x']
        server = self.get_server(
            mock_wsconn, {'werkzeug.socket': mock_socket},
            events=[
                [TextMessage('hello')],
                [Pong()],
            ], ping_interval=25, thread_class=mock.MagicMock(),
            selector_class=mock_sel)
        server._thread()
        assert mock_socket.send.call_count == 4
        assert mock_socket.send.call_args_list[1][0][0].startswith(b'Ping')
        assert mock_socket.send.call_args_list[2][0][0].startswith(b'Ping')
        assert mock_socket.send.call_args_list[3][0][0].startswith(b'Close')

    @mock.patch('simple_websocket.ws.WSConnection')
    def test_subprotocols(self, mock_wsconn):
        mock_socket = mock.MagicMock()
        mock_socket.recv.return_value = b'x'

        server = self.get_server(mock_wsconn, {
            'werkzeug.socket': mock_socket,
        }, client_subprotocols=['foo', 'bar'], server_subprotocols='bar')
        while server.connected:
            time.sleep(0.01)
        assert server.subprotocol == 'bar'

        server = self.get_server(mock_wsconn, {
            'werkzeug.socket': mock_socket,
        }, client_subprotocols=['foo', 'bar'], server_subprotocols=['bar'])
        while server.connected:
            time.sleep(0.01)
        assert server.subprotocol == 'bar'

        server = self.get_server(mock_wsconn, {
            'werkzeug.socket': mock_socket,
        }, client_subprotocols=['foo'], server_subprotocols=['foo', 'bar'])
        while server.connected:
            time.sleep(0.01)
        assert server.subprotocol == 'foo'

        server = self.get_server(mock_wsconn, {
            'werkzeug.socket': mock_socket,
        }, client_subprotocols=['foo'], server_subprotocols=['bar', 'baz'])
        while server.connected:
            time.sleep(0.01)
        assert server.subprotocol is None

        server = self.get_server(mock_wsconn, {
            'werkzeug.socket': mock_socket,
        }, client_subprotocols=['foo'], server_subprotocols=None)
        while server.connected:
            time.sleep(0.01)
        assert server.subprotocol is None
