from aiohttp import web
import simple_websocket

app = web.Application()


async def echo(request):
    ws = simple_websocket.AioServer(request)
    await ws.connect()
    try:
        while True:
            data = await ws.receive()
            await ws.send(data)
    except simple_websocket.ConnectionClosed:
        pass
    return web.Response(text='')


app.add_routes([web.get('/echo', echo)])

if __name__ == '__main__':
    web.run_app(app, port=5000)
