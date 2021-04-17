#import eventlet
#eventlet.monkey_patch()
#from eventlet import wsgi

#from gevent import monkey
#monkey.patch_all()
#from gevent.pywsgi import WSGIServer

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

#wsgi.server(eventlet.listen(('', 5000)), app)
#WSGIServer(('127.0.0.1', 5000), app).serve_forever()
