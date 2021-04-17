import simple_websocket


def main():
    ws = simple_websocket.Client('ws://localhost:5000/echo')
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
