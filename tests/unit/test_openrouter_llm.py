import json

import httpx2
import pytest
from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError

from app.adapters.openrouter_llm import OpenRouterClient


class Answer(BaseModel):
    text: str
    score: int


def _chat_completion_response(content: str) -> httpx2.Response:
    body = {
        "id": "chatcmpl-1",
        "object": "chat.completion",
        "created": 0,
        "model": "test-model",
        "choices": [
            {
                "index": 0,
                "finish_reason": "stop",
                "message": {"role": "assistant", "content": content},
            }
        ],
    }
    return httpx2.Response(200, json=body)


def make_client(handler) -> OpenRouterClient:
    http_client = httpx2.AsyncClient(transport=httpx2.MockTransport(handler))
    openai_client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key="test-key",
        http_client=http_client,
        max_retries=0,
    )
    return OpenRouterClient(api_key="test-key", client=openai_client)


class TestOpenRouterClient:
    async def test_returns_plain_string_without_response_model(self) -> None:
        captured: list[httpx2.Request] = []

        def handler(request: httpx2.Request) -> httpx2.Response:
            captured.append(request)
            return _chat_completion_response("hello there")

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

        def handler(request: httpx2.Request) -> httpx2.Response:
            return _chat_completion_response(payload)

        client = make_client(handler)

        result = await client.complete(system="sys", user="rate this", response_model=Answer)

        assert result == Answer(text="great", score=9)

    async def test_strips_json_code_fence(self) -> None:
        payload = "```json\n" + json.dumps({"text": "great", "score": 9}) + "\n```"

        def handler(request: httpx2.Request) -> httpx2.Response:
            return _chat_completion_response(payload)

        client = make_client(handler)

        result = await client.complete(system="sys", user="rate this", response_model=Answer)

        assert result == Answer(text="great", score=9)

    async def test_invalid_json_with_response_model_raises(self) -> None:
        def handler(request: httpx2.Request) -> httpx2.Response:
            return _chat_completion_response("not json at all")

        client = make_client(handler)

        with pytest.raises(ValidationError):
            await client.complete(system="sys", user="rate this", response_model=Answer)

    async def test_retries_after_transient_failure(self) -> None:
        calls = 0

        def handler(request: httpx2.Request) -> httpx2.Response:
            nonlocal calls
            calls += 1
            if calls == 1:
                return httpx2.Response(503, json={"error": "service unavailable"})
            return _chat_completion_response("hello there")

        client = make_client(handler)

        result = await client.complete(system="sys", user="hi")

        assert result == "hello there"
        assert calls == 2
