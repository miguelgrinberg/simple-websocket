from flask import Flask, render_template, request
from simple_websocket.aiows import Server
import simple_websocket
app = Flask(__name__)


@app.route('/echo', websocket=True)
def echo():
    ws = Server(request.environ)
    ws.connect()
    try:
        while True:
            data = ws.receive()
            ws.send(data)
    except simple_websocket.ConnectionClosed:
        pass
    return ''


if __name__ == '__main__':
    app.run()
