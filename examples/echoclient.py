from simple_websocket import Client, ConnectionClosed


def main():
    ws = Client.connect('ws://localhost:5000/echo')
    try:
        while True:
            data = input('> ')
            ws.send(data)
            data = ws.receive()
            print(f'< {data}')
    except (KeyboardInterrupt, EOFError, ConnectionClosed):
        ws.close()


if __name__ == '__main__':
    main()
