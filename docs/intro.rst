Installation
------------

This package is installed with ``pip``::

    pip install simple-websocket

Server Example
--------------

::

    from flask import Flask, render_template, request
    import simple_websocket
    app = Flask(__name__)


    @app.route('/echo', websocket=True)
    def echo():
        ws = simple_websocket.Server(request.environ)
        try:
            while True:
                data = ws.receive()
                ws.send(data)
        except simple_websocket.ConnectionClosed:
            pass
        return ''

    if __name__ == '__main__':
        app.run()

Client Example
--------------

::

    import simple_websocket

    def main():
        ws = simple_websocket.Client('ws://localhost:5000/echo')
        try:
            while True:
                data = input('> ')
                ws.send(data)
                data = ws.receive()
                print(f'< {data}')
        except (KeyboardInterrupt, EOFError, simple_websocket.ConnectionClosed):
            ws.close()

    if __name__ == '__main__':
        main()
