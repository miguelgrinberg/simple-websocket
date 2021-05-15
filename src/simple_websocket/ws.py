import socket
import ssl
import threading
from urllib.parse import urlsplit

from wsproto import ConnectionType, WSConnection
from wsproto.events import (
    AcceptConnection,
    RejectConnection,
    CloseConnection,
    Message,
    Request,
    Ping,
    TextMessage,
    BytesMessage,
)
from wsproto.frame_protocol import CloseReason
from wsproto.utilities import LocalProtocolError


class ConnectionError(RuntimeError):
    def __init__(self, status_code):
        self.status_code = status_code
        super().__init__(f'Connection error {status_code}')


class ConnectionClosed(RuntimeError):
    pass


class Base:
    def __init__(self, sock=None, connection_type=None, receive_bytes=4096,
                 thread_class=threading.Thread, event_class=threading.Event):
        self.sock = sock
        self.receive_bytes = receive_bytes
        self.input_buffer = []
        self.event = event_class()
        self.connected = False
        self.is_server = (connection_type == ConnectionType.SERVER)

        self.ws = WSConnection(connection_type)
        self.handshake()

        self.thread = thread_class(target=self._thread)
        self.thread.start()
        self.event.wait()
        self.event.clear()

    def handshake(self):
        """To be implemented by subclasses."""
        pass

    def send(self, data):
        if not self.connected:
            raise ConnectionClosed()
        if isinstance(data, bytes):
            out_data = self.ws.send(Message(data=data))
        else:
            out_data = self.ws.send(TextMessage(data=str(data)))
        self.sock.send(out_data)

    def receive(self, timeout=None):
        while self.connected and not self.input_buffer:
            if not self.event.wait(timeout=timeout):
                return None
            self.event.clear()
        if not self.connected:
            raise ConnectionClosed()
        return self.input_buffer.pop(0)

    def close(self, reason=None, message=None):
        out_data = self.ws.send(CloseConnection(
            reason or CloseReason.NORMAL_CLOSURE, message))
        try:
            self.sock.send(out_data)
        except BrokenPipeError:
            pass

    def _thread(self):
        self.connected = self._handle_events()
        self.event.set()
        while self.connected:
            try:
                in_data = self.sock.recv(self.receive_bytes)
            except (OSError, ConnectionResetError):
                self.connected = False
                self.event.set()
                break
            self.ws.receive_data(in_data)
            self.connected = self._handle_events()

    def _handle_events(self):
        keep_going = True
        out_data = b''
        for event in self.ws.events():
            try:
                if isinstance(event, Request):
                    out_data += self.ws.send(AcceptConnection())
                elif isinstance(event, CloseConnection):
                    if self.is_server:
                        out_data += self.ws.send(event.response())
                    self.event.set()
                    keep_going = False
                elif isinstance(event, Ping):
                    out_data += self.ws.send(event.response())
                elif isinstance(event, TextMessage):
                    self.input_buffer.append(event.data)
                    self.event.set()
                elif isinstance(event, BytesMessage):
                    self.input_buffer.append(event.data)
                    self.event.set()
            except LocalProtocolError:
                out_data = b''
                self.event.set()
                keep_going = False
        if out_data:
            self.sock.send(out_data)
        return keep_going


class Server(Base):
    def __init__(self, environ, receive_bytes=4096,
                 thread_class=threading.Thread, event_class=threading.Event):
        self.environ = environ
        if 'werkzeug.socket' in environ:
            # extract socket from Werkzeug's WSGI environment
            sock = environ.get('werkzeug.socket')
        elif 'gunicorn.socket' in environ:
            # extract socket from Gunicorn WSGI environment
            sock = environ.get('gunicorn.socket')
        elif 'eventlet.input' in environ:
            # extract socket from Eventlet's WSGI environment
            sock = environ.get('eventlet.input').get_socket()
        elif environ.get('SERVER_SOFTWARE', '').startswith('gevent'):
            # extract socket from Gevent's WSGI environment
            sock = environ['wsgi.input'].raw._sock
        else:
            raise RuntimeError('Cannot obtain socket from WSGI environment.')
        super().__init__(sock, connection_type=ConnectionType.SERVER,
                         receive_bytes=receive_bytes,
                         thread_class=thread_class, event_class=event_class)

    def handshake(self):
        in_data = b'GET / HTTP/1.1\r\n'
        for key, value in self.environ.items():
            if key.startswith('HTTP_'):
                header = '-'.join([p.capitalize() for p in key[5:].split('_')])
                in_data += f'{header}: {value}\r\n'.encode()
        in_data += b'\r\n'
        self.ws.receive_data(in_data)


class Client(Base):
    def __init__(self, url, receive_bytes=4096, thread_class=threading.Thread,
                 event_class=threading.Event, ssl_context=None):
        parsed_url = urlsplit(url)
        is_secure = parsed_url.scheme in ['https', 'wss']
        self.host = parsed_url.hostname
        self.port = parsed_url.port or (443 if is_secure else 80)
        self.path = parsed_url.path
        if parsed_url.query:
            self.path += '?' + parsed_url.query

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if is_secure:
            if ssl_context is None:
                ssl_context = ssl.create_default_context(
                    purpose=ssl.Purpose.SERVER_AUTH)
            sock = ssl_context.wrap_socket(sock, server_hostname=self.host)
        sock.connect((self.host, self.port))
        super().__init__(sock, connection_type=ConnectionType.CLIENT,
                         receive_bytes=receive_bytes,
                         thread_class=thread_class, event_class=event_class)

    def handshake(self):
        out_data = self.ws.send(Request(host=self.host, target=self.path))
        self.sock.send(out_data)

        in_data = self.sock.recv(self.receive_bytes)
        self.ws.receive_data(in_data)
        for event in self.ws.events():
            if isinstance(event, AcceptConnection):
                break
            elif isinstance(event, RejectConnection):
                raise ConnectionError(event.status_code)

    def close(self, reason=None, message=None):
        super().close(reason=reason, message=message)
        self.sock.close()
