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
