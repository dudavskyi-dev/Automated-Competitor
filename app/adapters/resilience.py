import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

T = TypeVar("T")

DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_TIMEOUT_SECONDS = 15.0


async def call_with_retry(
    func: Callable[[], Awaitable[T]],
    *,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> T:
    async for attempt in AsyncRetrying(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=0.1, max=2),
        reraise=True,
    ):
        with attempt:
            return await asyncio.wait_for(func(), timeout=timeout_seconds)
    raise AssertionError("unreachable: AsyncRetrying always returns or raises")
