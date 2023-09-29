from simple_websocket import AioServer, ConnectionClosed


async def echo(scope, receive, send):
    ws = await AioServer.accept(asgi=(scope, receive, send))
    try:
        while True:
            data = await ws.receive()
            await ws.send(data)
    except ConnectionClosed:
        pass
