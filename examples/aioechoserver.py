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
