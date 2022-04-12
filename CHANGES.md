# simple-websocket change log

**Release 0.5.2** - 2022-04-12

- Compression support [#11](https://github.com/miguelgrinberg/simple-websocket/issues/11) ([commit](https://github.com/miguelgrinberg/simple-websocket/commit/9277e67140a456bd34e09146732d4bdca0c6db12))
- Update builds for python 3.10 and pypy3.8 ([commit](https://github.com/miguelgrinberg/simple-websocket/commit/f44674fd8ec42b05e6ebc0571cb53ba60d3ce144))

**Release 0.5.1** - 2022-02-17

- Store the detected WebSocket mode in server ([commit](https://github.com/miguelgrinberg/simple-websocket/commit/145e3be63ad1de75eedbcfc193eb304767607bc8))

**Release 0.5.0** - 2021-12-04

- Added optional WebSocket Ping/Pong mechanism [#6](https://github.com/miguelgrinberg/simple-websocket/issues/6) ([commit](https://github.com/miguelgrinberg/simple-websocket/commit/6f13cdf74abf8627af53e03df2e84db204392a21))
- Option to set a maximum message size [#5](https://github.com/miguelgrinberg/simple-websocket/issues/5) ([commit](https://github.com/miguelgrinberg/simple-websocket/commit/b285024fc3fd75910d166fa5ad258490b70d1326))
- Store close reason in `ConnectionClosed` exception [#9](https://github.com/miguelgrinberg/simple-websocket/issues/9) ([commit](https://github.com/miguelgrinberg/simple-websocket/commit/91eaa52c659e69307e1b3a64329aafc81e3b4625))
- Option configure a custom selector class ([commit](https://github.com/miguelgrinberg/simple-websocket/commit/1b3dcf77c2aba7ccc6b0f108744f46575ef190b8))

**Release 0.4.0** - 2021-09-23

- Close the connection if `socket.recv()` returns 0 bytes [#4](https://github.com/miguelgrinberg/simple-websocket/issues/4) ([commit](https://github.com/miguelgrinberg/simple-websocket/commit/6a75a742fe28ef6fe30ca901144478c466640967))

**Release 0.3.0** - 2021-08-05

- Handle older versions of gevent [#3](https://github.com/miguelgrinberg/simple-websocket/issues/3) ([commit](https://github.com/miguelgrinberg/simple-websocket/commit/5ce50802d053bf04d1f6f8c43569105bc5c0b389))
- Handle large messages split during transmission [#2](https://github.com/miguelgrinberg/simple-websocket/issues/2) ([commit](https://github.com/miguelgrinberg/simple-websocket/commit/e16058daf6d0329028b7f9b81f65f13b64e8e45b))
- Documentation ([commit](https://github.com/miguelgrinberg/simple-websocket/commit/02cbe78c723b298af9114989c41b8660b8aad3fb))
- GitHub builds ([commit](https://github.com/miguelgrinberg/simple-websocket/commit/e846f0f86f8bdfed6fb2e7f5fff62abad6de518c))
- Unit tests

**Release 0.2.0** - 2021-05-15

- Make the closing of the connection more resilient to errors ([commit](https://github.com/miguelgrinberg/simple-websocket/commit/6cdf24a8fc1fb782db968e6d4526cced6984d5a4))
- Unit testing framework ([commit](https://github.com/miguelgrinberg/simple-websocket/commit/35de1658593a153b6926f05b3e3b2eadda814a47))

**Release 0.1.0** - 2021-04-18

- initial commit ([commit](https://github.com/miguelgrinberg/simple-websocket/commit/1ddd63d230950f40683a7771eb3ce6ae7d199c23))
