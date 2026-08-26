import asyncio

import pytest

from app.adapters.resilience import call_with_retry


class TestCallWithRetry:
    async def test_succeeds_on_first_attempt(self) -> None:
        calls = 0

        async def func() -> str:
            nonlocal calls
            calls += 1
            return "ok"

        result = await call_with_retry(func, max_attempts=3, timeout_seconds=1.0)

        assert result == "ok"
        assert calls == 1

    async def test_retries_until_success(self) -> None:
        calls = 0

        async def func() -> str:
            nonlocal calls
            calls += 1
            if calls < 3:
                raise ValueError("transient failure")
            return "ok"

        result = await call_with_retry(func, max_attempts=5, timeout_seconds=1.0)

        assert result == "ok"
        assert calls == 3

    async def test_raises_after_exhausting_attempts(self) -> None:
        calls = 0

        async def func() -> str:
            nonlocal calls
            calls += 1
            raise ValueError("permanent failure")

        with pytest.raises(ValueError, match="permanent failure"):
            await call_with_retry(func, max_attempts=3, timeout_seconds=1.0)

        assert calls == 3

    async def test_timeout_raises_after_retries(self) -> None:
        calls = 0

        async def func() -> str:
            nonlocal calls
            calls += 1
            await asyncio.sleep(1.0)
            return "too slow"

        with pytest.raises(TimeoutError):
            await call_with_retry(func, max_attempts=2, timeout_seconds=0.02)

        assert calls == 2
