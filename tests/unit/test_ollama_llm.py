import json

import httpx
import pytest
from ollama import AsyncClient
from pydantic import BaseModel

from app.adapters.ollama_llm import OllamaClient


class Answer(BaseModel):
    text: str
    score: int


def _chat_response(content: str) -> httpx.Response:
    body = {
        "model": "qwen2.5:3b",
        "created_at": "2026-08-28T00:00:00Z",
        "message": {"role": "assistant", "content": content},
        "done": True,
    }
    return httpx.Response(200, json=body)


def make_client(handler) -> OllamaClient:
    transport = httpx.MockTransport(handler)
    ollama_client = AsyncClient(host="http://localhost:11434", transport=transport)
    return OllamaClient(client=ollama_client)


class TestOllamaClient:
    async def test_returns_plain_string_without_response_model(self) -> None:
        captured: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(request)
            return _chat_response("hello there")

        client = make_client(handler)

        result = await client.complete(system="sys prompt", user="hi")

        assert result == "hello there"
        body = json.loads(captured[0].content)
        assert body["messages"] == [
            {"role": "system", "content": "sys prompt"},
            {"role": "user", "content": "hi"},
        ]

    async def test_parses_response_model(self) -> None:
        payload = json.dumps({"text": "great", "score": 9})

        def handler(request: httpx.Request) -> httpx.Response:
            return _chat_response(payload)

        client = make_client(handler)

        result = await client.complete(system="sys", user="rate this", response_model=Answer)

        assert result == Answer(text="great", score=9)

    async def test_retries_after_transient_failure(self) -> None:
        calls = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal calls
            calls += 1
            if calls == 1:
                return httpx.Response(503, json={"error": "service unavailable"})
            return _chat_response("hello there")

        client = make_client(handler)

        result = await client.complete(system="sys", user="hi")

        assert result == "hello there"
        assert calls == 2

    async def test_schema_mismatch_retries_then_succeeds(self) -> None:
        calls = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal calls
            calls += 1
            if calls == 1:
                return _chat_response("not json at all")
            return _chat_response(json.dumps({"text": "great", "score": 9}))

        client = make_client(handler)

        result = await client.complete(system="sys", user="rate this", response_model=Answer)

        assert result == Answer(text="great", score=9)
        assert calls == 2

    async def test_schema_mismatch_exhausts_retries_then_raises(self) -> None:
        calls = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal calls
            calls += 1
            return _chat_response("not json at all")

        client = make_client(handler)

        with pytest.raises(Exception):  # noqa: B017 - pydantic ValidationError
            await client.complete(system="sys", user="rate this", response_model=Answer)

        assert calls == 3

    async def test_connection_error_raises_clearly(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("Connection refused")

        client = make_client(handler)

        with pytest.raises(ConnectionError):
            await client.complete(system="sys", user="hi")
