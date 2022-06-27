import selectors
import socket
import ssl
from time import time
from urllib.parse import urlsplit

from wsproto import ConnectionType, WSConnection
from wsproto.events import (
    AcceptConnection,
    RejectConnection,
    CloseConnection,
    Message,
    Request,
    Ping,
    Pong,
    TextMessage,
    BytesMessage,
)
from wsproto.extensions import PerMessageDeflate
from wsproto.frame_protocol import CloseReason
from wsproto.utilities import LocalProtocolError


class ConnectionError(RuntimeError):  # pragma: no cover
    """Connection error exception class."""
    def __init__(self, status_code=None):
        self.status_code = status_code
        super().__init__(f'Connection error: {status_code}')


class ConnectionClosed(RuntimeError):
    """Connection closed exception class."""
    def __init__(self, reason=CloseReason.NO_STATUS_RCVD, message=None):
        self.reason = reason
        self.message = message
        super().__init__(f'Connection closed: {reason} {message or ""}')


class Base:
    def __init__(self, sock=None, connection_type=None, receive_bytes=4096,
                 ping_interval=None, max_message_size=None,
                 thread_class=None, event_class=None, selector_class=None):
        self.sock = sock
        self.receive_bytes = receive_bytes
        self.ping_interval = ping_interval
        self.max_message_size = max_message_size
        self.pong_received = True
        self.input_buffer = []
        self.incoming_message = None
        self.connected = False
        self.is_server = (connection_type == ConnectionType.SERVER)
        self.close_reason = CloseReason.NO_STATUS_RCVD
        self.close_message = None

        if thread_class is None:
            import threading
            thread_class = threading.Thread
        if event_class is None:  # pragma: no branch
            import threading
            event_class = threading.Event
        if selector_class is None:
            import selectors
            selector_class = selectors.DefaultSelector

        self.event = event_class()
        self.selector = selector_class()

        self.ws = WSConnection(connection_type)
        self.handshake()

        if not self.connected:  # pragma: no cover
            raise ConnectionError()
        self.thread = thread_class(target=self._thread)
        self.thread.start()

    def handshake(self):  # pragma: no cover
        # to be implemented by subclasses
        pass

    def send(self, data):
        """Send data over the WebSocket connection.

        :param data: The data to send. If ``data`` is of type ``bytes``, then
                     a binary message is sent. Else, the message is sent in
                     text format.
        """
        if not self.connected:
            raise ConnectionClosed(self.close_reason, self.close_message)
        if isinstance(data, bytes):
            out_data = self.ws.send(Message(data=data))
        else:
            out_data = self.ws.send(TextMessage(data=str(data)))
        self.sock.send(out_data)

    def receive(self, timeout=None):
        """Receive data over the WebSocket connection.

        :param timeout: Amount of time to wait for the data, in seconds. Set
                        to ``None`` (the default) to wait undefinitely. Set
                        to 0 to read without blocking.

        The data received is returned, as ``bytes`` or ``str``, depending on
        the type of the incoming message.
        """
        while self.connected and not self.input_buffer:
            if not self.event.wait(timeout=timeout):
                return None
            self.event.clear()
        if not self.connected:  # pragma: no cover
            raise ConnectionClosed(self.close_reason, self.close_message)
        return self.input_buffer.pop(0)

    def close(self, reason=None, message=None):
        """Close the WebSocket connection.

        :param reason: A numeric status code indicating the reason of the
                       closure, as defined by the WebSocket specifiation. The
                       default is 1000 (normal closure).
        :param message: A text message to be sent to the other side.
        """
        if not self.connected:
            raise ConnectionClosed(self.close_reason, self.close_message)
        out_data = self.ws.send(CloseConnection(
            reason or CloseReason.NORMAL_CLOSURE, message))
        try:
            self.sock.send(out_data)
        except BrokenPipeError:  # pragma: no cover
            pass
        self.connected = False

    def _thread(self):
        sel = None
        if self.ping_interval:
            next_ping = time() + self.ping_interval
            sel = self.selector
            sel.register(self.sock, selectors.EVENT_READ, True)

        while self.connected:
            try:
                if sel:
                    now = time()
                    if not sel.select(next_ping - now):
                        # we reached the timeout, we have to send a ping
                        if not self.pong_received:
                            self.close(reason=CloseReason.POLICY_VIOLATION,
                                       message='Ping/Pong timeout')
                            break
                        self.pong_received = False
                        self.sock.send(self.ws.send(Ping()))
                        next_ping += self.ping_interval
                        continue
                in_data = self.sock.recv(self.receive_bytes)
                if len(in_data) == 0:
                    raise OSError()
            except (OSError, ConnectionResetError):  # pragma: no cover
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
                    out_data += self.ws.send(AcceptConnection(
                        extensions=[PerMessageDeflate()]))
                elif isinstance(event, CloseConnection):
                    if self.is_server:
                        out_data += self.ws.send(event.response())
                    self.close_reason = event.code
                    self.close_message = event.reason
                    self.event.set()
                    keep_going = False
                elif isinstance(event, Ping):
                    out_data += self.ws.send(event.response())
                elif isinstance(event, Pong):
                    self.pong_received = True
                elif isinstance(event, TextMessage):
                    if self.max_message_size and \
                            len(event.data) > self.max_message_size:
                        out_data += self.ws.send(CloseConnection(
                            CloseReason.MESSAGE_TOO_BIG, 'Message is too big'))
                        self.event.set()
                        keep_going = False
                        break
                    if self.incoming_message is None:
                            self.incoming_message = event.data
                    else:
                        self.incoming_message += event.data
                    if not event.message_finished:
                        continue
                    self.input_buffer.append(self.incoming_message)
                    self.incoming_message = None
                    self.event.set()
                elif isinstance(event, BytesMessage):
                    if self.max_message_size and \
                            len(event.data) > self.max_message_size:
                        out_data += self.ws.send(CloseConnection(
                            CloseReason.MESSAGE_TOO_BIG, 'Message is too big'))
                        self.event.set()
                        keep_going = False
                        break
                    if self.incoming_message is None:
                        self.incoming_message = bytearray(event.data)
                    else:
                        self.incoming_message += event.data
                    if not event.message_finished:
                        continue
                    self.input_buffer.append(self.incoming_message)
                    self.incoming_message = None
                    self.event.set()
                else:  # pragma: no cover
                    pass
            except LocalProtocolError:  # pragma: no cover
                out_data = b''
                self.event.set()
                keep_going = False
        if out_data:
            self.sock.send(out_data)
        return keep_going


class Server(Base):
    """This class implements a WebSocket server.

    :param environ: A WSGI ``environ`` dictionary with the request details.
                    Among other things, this class expects to find the
                    low-level network socket for the connection somewhere in
                    this dictionary. Since the WSGI specification does not
                    cover where or how to store this socket, each web server
                    does this in its own different way. Werkzeug, Gunicorn,
                    Eventlet and Gevent are the only web servers that are
                    currently supported.
    :param receive_bytes: The size of the receive buffer, in bytes. The
                          default is 4096.
    :param ping_interval: Send ping packets to clients at the requested
                          interval in seconds. Set to ``None`` (the default) to
                          disable ping/pong logic. Enable to prevent
                          disconnections when the line is idle for a certain
                          amount of time, or to detect unresponsive clients and
                          disconnect them. A recommended interval is 25
                          seconds.
    :param max_message_size: The maximum size allowed for a message, in bytes,
                             or ``None`` for no limit. The default is ``None``.
    :param thread_class: The ``Thread`` class to use when creating background
                         threads. The default is the ``threading.Thread``
                         class from the Python standard library.
    :param event_class: The ``Event`` class to use when creating event
                        objects. The default is the `threading.Event`` class
                        from the Python standard library.
    :param selector_class: The ``Selector`` class to use when creating
                           selectors. The default is the
                           ``selectors.DefaultSelector`` class from the Python
                           standard library.
    """
    def __init__(self, environ, receive_bytes=4096, ping_interval=None,
                 max_message_size=None, thread_class=None, event_class=None,
                 selector_class=None):
        self.environ = environ
        self.mode = 'unknown'
        sock = None
        if 'werkzeug.socket' in environ:
            # extract socket from Werkzeug's WSGI environment
            sock = environ.get('werkzeug.socket')
            self.mode = 'werkzeug'
        elif 'gunicorn.socket' in environ:
            # extract socket from Gunicorn WSGI environment
            sock = environ.get('gunicorn.socket')
            self.mode = 'gunicorn'
        elif 'eventlet.input' in environ:  # pragma: no cover
            # extract socket from Eventlet's WSGI environment
            sock = environ.get('eventlet.input').get_socket()
            self.mode = 'eventlet'
        elif environ.get('SERVER_SOFTWARE', '').startswith(
                'gevent'):  # pragma: no cover
            # extract socket from Gevent's WSGI environment
            wsgi_input = environ['wsgi.input']
            if not hasattr(wsgi_input, 'raw') and hasattr(wsgi_input, 'rfile'):
                wsgi_input = wsgi_input.rfile
            if hasattr(wsgi_input, 'raw'):
                sock = wsgi_input.raw._sock
                self.mode = 'gevent'
        if sock is None:
            raise RuntimeError('Cannot obtain socket from WSGI environment.')
        super().__init__(sock, connection_type=ConnectionType.SERVER,
                         receive_bytes=receive_bytes,
                         ping_interval=ping_interval,
                         max_message_size=max_message_size,
                         thread_class=thread_class, event_class=event_class,
                         selector_class=selector_class)

    def handshake(self):
        in_data = b'GET / HTTP/1.1\r\n'
        for key, value in self.environ.items():
            if key.startswith('HTTP_'):
                header = '-'.join([p.capitalize() for p in key[5:].split('_')])
                in_data += f'{header}: {value}\r\n'.encode()
        in_data += b'\r\n'
        self.ws.receive_data(in_data)
        self.connected = self._handle_events()


class Client(Base):
    """This class implements a WebSocket client.

    :param url: The connection URL. Both ``ws://`` and ``wss://`` URLs are
                accepted.
    :param receive_bytes: The size of the receive buffer, in bytes. The
                          default is 4096.
    :param ping_interval: Send ping packets to the server at the requested
                          interval in seconds. Set to ``None`` (the default) to
                          disable ping/pong logic. Enable to prevent
                          disconnections when the line is idle for a certain
                          amount of time, or to detect an unresponsive server
                          and disconnect. A recommended interval is 25 seconds.
                          In general it is preferred to enable ping/pong on the
                          server, and let the client respond with pong (which
                          it does regardless of this setting).
    :param max_message_size: The maximum size allowed for a message, in bytes,
                             or ``None`` for no limit. The default is ``None``.
    :param ssl_context: An ``SSLContext`` instance, if a default SSL context
                        isn't sufficient.
    :param thread_class: The ``Thread`` class to use when creating background
                         threads. The default is the ``threading.Thread``
                         class from the Python standard library.
    :param event_class: The ``Event`` class to use when creating event
                        objects. The default is the `threading.Event`` class
                        from the Python standard library.
    """
    def __init__(self, url, receive_bytes=4096, ping_interval=None,
                 max_message_size=None, ssl_context=None, thread_class=None,
                 event_class=None, selector_class=None):
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
                         ping_interval=ping_interval,
                         max_message_size=max_message_size,
                         thread_class=thread_class, event_class=event_class)

    def handshake(self):
        out_data = self.ws.send(Request(host=self.host, target=self.path))
        self.sock.send(out_data)

        in_data = self.sock.recv(self.receive_bytes)
        self.ws.receive_data(in_data)
        event = next(self.ws.events())
        if isinstance(event, RejectConnection):  # pragma: no cover
            raise ConnectionError(event.status_code)
        elif not isinstance(event, AcceptConnection):  # pragma: no cover
            raise ConnectionError(400)
        self.connected = True

    def close(self, reason=None, message=None):
        super().close(reason=reason, message=message)
        self.sock.close()
