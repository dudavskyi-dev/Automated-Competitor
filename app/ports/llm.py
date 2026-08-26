from typing import Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


@runtime_checkable
class LLMClient(Protocol):
    async def complete(
        self, system: str, user: str, response_model: type[T] | None = None
    ) -> T | str: ...
