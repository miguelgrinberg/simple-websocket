import asyncio
from unittest import mock


def AsyncMock(*args, **kwargs):
    """Return a mock asynchronous function."""
    m = mock.MagicMock(*args, **kwargs)

    async def mock_coro(*args, **kwargs):
        return m(*args, **kwargs)

    mock_coro.mock = m
    return mock_coro


def _run(coro):
    """Run the given coroutine."""
    return asyncio.get_event_loop().run_until_complete(coro)


def make_sync(coro):
    """Wrap a coroutine so that it can be executed by pytest."""
    def wrapper(*args, **kwargs):
        return _run(coro(*args, **kwargs))
    return wrapper
