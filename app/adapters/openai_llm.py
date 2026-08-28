from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

from app.adapters.resilience import call_with_retry
from app.ports.llm import T

DEFAULT_MODEL = "gpt-5-mini"


class OpenAIClient:
    def __init__(
        self, api_key: str, model: str = DEFAULT_MODEL, client: AsyncOpenAI | None = None
    ) -> None:
        self._client = client or AsyncOpenAI(api_key=api_key, max_retries=0)
        self._model = model

    async def complete(
        self, system: str, user: str, response_model: type[T] | None = None
    ) -> T | str:
        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

        async def _do() -> T | str:
            if response_model is None:
                response = await self._client.chat.completions.create(
                    model=self._model, messages=messages
                )
                return response.choices[0].message.content or ""
            # OpenAI's native schema-constrained JSON mode: a non-conforming
            # response raises pydantic.ValidationError directly from .parse(),
            # which call_with_retry catches and retries as a fresh call.
            completion = await self._client.chat.completions.parse(
                model=self._model, messages=messages, response_format=response_model
            )
            return completion.choices[0].message.parsed  # type: ignore[return-value]

        return await call_with_retry(_do)
