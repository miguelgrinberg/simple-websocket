import simple_websocket
from simple_websocket.aiows import Client


def main():
    ws = Client('ws://localhost:5000/echo')
    ws.connect()
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
