import asyncio
import simple_websocket


async def main():
    ws = simple_websocket.AioClient('ws://localhost:5000/echo')
    await ws.connect()
    try:
        while True:
            data = input('> ')
            await ws.send(data)
            data = await ws.receive()
            print(f'< {data}')
    except (KeyboardInterrupt, EOFError, simple_websocket.ConnectionClosed):
        await ws.close()


if __name__ == '__main__':
    asyncio.run(main())
