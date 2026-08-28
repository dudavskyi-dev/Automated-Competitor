from ollama import AsyncClient

from app.adapters.resilience import call_with_retry
from app.ports.llm import T

DEFAULT_MODEL = "qwen2.5:3b"
DEFAULT_HOST = "http://localhost:11434"


class OllamaClient:
    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        host: str = DEFAULT_HOST,
        client: AsyncClient | None = None,
    ) -> None:
        self._client = client or AsyncClient(host=host)
        self._model = model
        # Local inference on modest/no-GPU hardware has no fixed upper bound on
        # latency, and there's no external quota pushing us to give up early -
        # wait as long as it takes rather than timing out a slow-but-legitimate
        # response.
        self._timeout_seconds: float | None = None

    async def complete(
        self, system: str, user: str, response_model: type[T] | None = None
    ) -> T | str:
        format_arg = response_model.model_json_schema() if response_model is not None else None

        async def _do() -> T | str:
            response = await self._client.chat(
                model=self._model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                format=format_arg,
            )
            content = response.message.content or ""
            if response_model is None:
                return content
            return response_model.model_validate_json(content)

        return await call_with_retry(_do, timeout_seconds=self._timeout_seconds)
