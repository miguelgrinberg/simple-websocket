# simple-websocket change log

**Release 1.0.0** - 2023-10-05

- New async client and server [#28](https://github.com/miguelgrinberg/simple-websocket/issues/28) ([commit](https://github.com/miguelgrinberg/simple-websocket/commit/57c5ffcb25c14d5c70f1ad4edd0261cdfcd27c94))
- On a closed connection, return buffered input before raising an exception [#30](https://github.com/miguelgrinberg/simple-websocket/issues/30) ([commit](https://github.com/miguelgrinberg/simple-websocket/commit/6c87abe22215c45b3dc0dadc168c3dd061eb2aa4))
- Do not duplicate SSLSocket instances [#26](https://github.com/miguelgrinberg/simple-websocket/issues/26) ([commit](https://github.com/miguelgrinberg/simple-websocket/commit/da42e98bf80f22747089946a6a08840e0bf646a9))
- Handle broken pipe errors in background thread [#29](https://github.com/miguelgrinberg/simple-websocket/issues/29) ([commit](https://github.com/miguelgrinberg/simple-websocket/commit/6f92764754550fc85b25e42182050c1e6636a41d))
- Remove unused argument ([commit](https://github.com/miguelgrinberg/simple-websocket/commit/245eedcf1e82fd3d199a6f7bf44916047588763d))
- Eliminate race conditions during testing [#27](https://github.com/miguelgrinberg/simple-websocket/issues/27) ([commit](https://github.com/miguelgrinberg/simple-websocket/commit/a37c79dc9ec8a54968d8b849c7f0a2e3bca46db8))
- Remove python 3.7 from unit tests ([commit](https://github.com/miguelgrinberg/simple-websocket/commit/761925a635901b4641ad63b6072c24ff5c4099d5))

**Release 0.10.1** - 2023-06-04

- Duplicate the gevent socket to avoid using it in multiple greenlets [#24](https://github.com/miguelgrinberg/simple-websocket/issues/24) ([commit](https://github.com/miguelgrinberg/simple-websocket/commit/ebc12b1a390ab36d8dcd020b45410da282fa8d60))
- Add Python 3.11 to builds ([commit](https://github.com/miguelgrinberg/simple-websocket/commit/df5c92a8d8b48e3482be5ad7af2628b17e6d6d07))

**Release 0.10.0** - 2023-04-08

- Support custom headers in the client ([commit](https://github.com/miguelgrinberg/simple-websocket/commit/4f5c653378e77026604b4b25b8a5373da48b5f74))

**Release 0.9.0** - 2022-11-17

- Properly clean up closed connections [#19](https://github.com/miguelgrinberg/simple-websocket/issues/19) ([commit](https://github.com/miguelgrinberg/simple-websocket/commit/9bda31010405045125b304afd633b9a9a5171335)) (thanks **Carlos Carvalho**!)

**Release 0.8.1** - 2022-09-11

- Correct handling of an empty subprotocol list in server [#22](https://github.com/miguelgrinberg/simple-websocket/issues/22) ([commit](https://github.com/miguelgrinberg/simple-websocket/commit/cf336163fbc65281163fac0c253c4281b760c169))
- Handshake robustness with slow clients such as microcontrollers ([commit](https://github.com/miguelgrinberg/simple-websocket/commit/271f8fc3ee466a0d0bd5a71543b2e50a632891dd))
- Prevent race condition on client close [#18](https://github.com/miguelgrinberg/simple-websocket/issues/18) ([commit](https://github.com/miguelgrinberg/simple-websocket/commit/e17449153b472a801df4bf2246f06a8486d91c9d))
- Improved documentation for subprotocol negotiation ([commit](https://github.com/miguelgrinberg/simple-websocket/commit/c74785482ff266c552692a330c3c71d2b9d1f438))

**Release 0.8.0** - 2022-08-08

- Support for subprotocol negotiation [#17](https://github.com/miguelgrinberg/simple-websocket/issues/17) ([commit](https://github.com/miguelgrinberg/simple-websocket/commit/04baf871e05e99d80c8905e9e9b0ff4be322e71f))

**Release 0.7.0** - 2022-07-24

- More robust handling of ping intervals [#16](https://github.com/miguelgrinberg/simple-websocket/issues/16) ([commit](https://github.com/miguelgrinberg/simple-websocket/commit/05185122a0d2548d5cbd7c3d650db9c9dd49fa76) [commit](https://github.com/miguelgrinberg/simple-websocket/commit/08bd663a918669fb12e805e08a73cae7d7aac3a1))

**Release 0.6.0** - 2022-07-15

- Improved performance of multi-part messages [#15](https://github.com/miguelgrinberg/simple-websocket/issues/15) ([commit](https://github.com/miguelgrinberg/simple-websocket/commit/ca2ea38520229ef7c881690667f23b99506f54a3))

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
