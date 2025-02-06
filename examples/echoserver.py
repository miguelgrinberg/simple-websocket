from flask import Flask, request, render_template
from simple_websocket import Server, ConnectionClosed

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/echo', websocket=True)
def echo():
    ws = Server.accept(request.environ)
    try:
        while True:
            data = ws.receive()
            if data == 'close':
                ws.close(reason=3000, message="goodbye!")
                break
            ws.send(data)
    except ConnectionClosed:
        pass
    return ''


if __name__ == '__main__':
    app.run()
