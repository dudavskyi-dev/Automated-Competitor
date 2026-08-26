import json

from openai import AsyncOpenAI

from app.ports.llm import T

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "meta-llama/llama-3.1-8b-instruct:free"


def _strip_code_fences(content: str) -> str:
    text = content.strip()
    if text.startswith("```"):
        text = text.removeprefix("```json").removeprefix("```")
        text = text.removesuffix("```")
    return text.strip()


class OpenRouterClient:
    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        client: AsyncOpenAI | None = None,
    ) -> None:
        self._client = client or AsyncOpenAI(base_url=OPENROUTER_BASE_URL, api_key=api_key)
        self._model = model

    async def complete(
        self, system: str, user: str, response_model: type[T] | None = None
    ) -> T | str:
        if response_model is not None:
            schema = json.dumps(response_model.model_json_schema())
            system = f"{system}\n\nRespond only with valid JSON matching this schema:\n{schema}"

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        content = response.choices[0].message.content or ""

        if response_model is None:
            return content
        return response_model.model_validate_json(_strip_code_fences(content))
