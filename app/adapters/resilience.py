import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

T = TypeVar("T")

DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_TIMEOUT_SECONDS = 15.0
# Free-tier LLM/search APIs commonly ask callers to wait 5-23s when rate-limited
# (see Retry-After on their 429s) - a sub-2s backoff never actually clears that.
DEFAULT_WAIT_MULTIPLIER = 1.0
DEFAULT_WAIT_MAX = 20.0


async def call_with_retry(
    func: Callable[[], Awaitable[T]],
    *,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    timeout_seconds: float | None = DEFAULT_TIMEOUT_SECONDS,
    wait_multiplier: float = DEFAULT_WAIT_MULTIPLIER,
    wait_max: float = DEFAULT_WAIT_MAX,
) -> T:
    async for attempt in AsyncRetrying(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=wait_multiplier, max=wait_max),
        reraise=True,
    ):
        with attempt:
            return await asyncio.wait_for(func(), timeout=timeout_seconds)
    raise AssertionError("unreachable: AsyncRetrying always returns or raises")
