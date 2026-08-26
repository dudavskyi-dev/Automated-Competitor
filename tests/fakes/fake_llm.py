from typing import Any

from pydantic import BaseModel

from app.ports.llm import T


class FakeLLM:
    def __init__(self, responses: list[Any]) -> None:
        self._responses = list(responses)
        self.calls: list[tuple[str, str, type[BaseModel] | None]] = []

    async def complete(
        self, system: str, user: str, response_model: type[T] | None = None
    ) -> T | str:
        self.calls.append((system, user, response_model))
        return self._responses.pop(0)
