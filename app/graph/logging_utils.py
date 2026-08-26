from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, TypeVar

import structlog

from app.graph.state import GraphState

Node = TypeVar("Node", bound=Callable[[Any, GraphState], Awaitable[GraphState]])


def log_node(name: str) -> Callable[[Node], Node]:
    def decorator(func: Node) -> Node:
        logger = structlog.get_logger(node=name)

        @wraps(func)
        async def wrapper(self: Any, state: GraphState) -> GraphState:
            logger.info("node_started")
            try:
                result = await func(self, state)
            except Exception:
                logger.exception("node_failed")
                raise

            failed = any(key.endswith("_failed") and value for key, value in result.items())
            logger.info("node_finished", output_keys=list(result.keys()), failed=failed)
            return result

        return wrapper  # type: ignore[return-value]

    return decorator
