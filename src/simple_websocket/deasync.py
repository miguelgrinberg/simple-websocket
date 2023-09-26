import asyncio
import functools
from threading import Thread


class DeAsync:
    _asyncio_thread = None
    _loop = asyncio.new_event_loop()

    def __init_subclass__(cls, async_class):
        super().__init_subclass__()
        cls.async_class = async_class

    def __init__(self, *args, **kwargs):
        if DeAsync._asyncio_thread is None:
            DeAsync._asyncio_thread = Thread(target=self._loop.run_forever)
            DeAsync._asyncio_thread.daemon = True
            DeAsync._asyncio_thread.start()
        self._async = self.async_class(*args, **kwargs)

    @staticmethod
    def property(name):
        def getter(self):
            return getattr(self._async, name)
        return property(getter)

    @staticmethod
    def method(fn):
        if not asyncio.iscoroutinefunction(fn):
            async def _fn(*args, **kwargs):
                return fn(*args, **kwargs)
        else:
            _fn = fn

        def getter(self, *args, **kwargs):
            return asyncio.run_coroutine_threadsafe(
                _fn(self._async, *args, **kwargs), self._loop).result()

        functools.update_wrapper(getter, fn)
        return getter
