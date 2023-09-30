Getting Started
===============

``simple-websocket`` includes a collection of WebSocket servers and clients for
Python, including support for both traditional and asynchronous (asyncio)
workflows. The servers are designed to be integrated into larger web
applications if desired.

Installation
------------

This package is installed with ``pip``::

    pip install simple-websocket

Server Example #1: Flask
------------------------

The following example shows how to add a WebSocket route to a
`Flask <https://flask.palletsprojects.com>`_ application.

::

    from flask import Flask, request
    from simple_websocket import Server, ConnectionClosed

    app = Flask(__name__)

    @app.route('/echo', websocket=True)
    def echo():
        ws = Server.accept(request.environ)
        try:
            while True:
                data = ws.receive()
                ws.send(data)
        except ConnectionClosed:
            pass
        return ''

Integration with web applications using other
`WSGI <https://wsgi.readthedocs.io>`_ frameworks works in a similar way. The
only requirement is to pass the ``environ`` dictionary to the
``Server.accept()`` method to initiate the WebSocket handshake.

Server Example #2: Aiohttp
--------------------------

The following example shows how to add a WebSocket route to a web application
built with the `aiohttp <https://aiohttp.readthedocs.io>`_ framework.

::

    from aiohttp import web
    from simple_websocket import AioServer, ConnectionClosed

    app = web.Application()

    async def echo(request):
        ws = await AioServer.accept(aiohttp=request)
        try:
            while True:
                data = await ws.receive()
                await ws.send(data)
        except ConnectionClosed:
            pass
        return web.Response(text='')

    app.add_routes([web.get('/echo', echo)])

    if __name__ == '__main__':
        web.run_app(app, port=5000)

Server Example #3: ASGI
-----------------------

The next server example shows an asynchronous application that supports the
`ASGI <https://asgi.readthedocs.io>`_ protocol.

::

    from simple_websocket import AioServer, ConnectionClosed

    async def echo(scope, receive, send):
        ws = await AioServer.accept(asgi=(scope, receive, send))
        try:
            while True:
                data = await ws.receive()
                await ws.send(data)
        except ConnectionClosed:
            pass
        
Client Example #1: Synchronous
------------------------------

The client example that follows can connect to any of the server examples above
using a synchronous interface.

::

    from simple_websocket import Client, ConnectionClosed

    def main():
        ws = Client.connect('ws://localhost:5000/echo')
        try:
            while True:
                data = input('> ')
                ws.send(data)
                data = ws.receive()
                print(f'< {data}')
        except (KeyboardInterrupt, EOFError, ConnectionClosed):
            ws.close()

    if __name__ == '__main__':
        main()

Client Example #2: Asynchronous
-------------------------------

The next client uses Python's ``asyncio`` framework.

::

    import asyncio
    from simple_websocket import AioClient, ConnectionClosed

    async def main():
        ws = await AioClient.connect('ws://localhost:5000/echo')
        try:
            while True:
                data = input('> ')
                await ws.send(data)
                data = await ws.receive()
                print(f'< {data}')
        except (KeyboardInterrupt, EOFError, ConnectionClosed):
            await ws.close()

    if __name__ == '__main__':
        asyncio.run(main())
