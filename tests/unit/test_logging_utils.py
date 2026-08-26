import pytest
import structlog

from app.graph.logging_utils import log_node


class Dummy:
    @log_node("dummy_node")
    async def __call__(self, state: dict) -> dict:
        if state.get("boom"):
            raise ValueError("kaboom")
        return {"result": "ok", "result_failed": state.get("should_fail", False)}


class TestLogNode:
    async def test_logs_started_and_finished_on_success(self) -> None:
        with structlog.testing.capture_logs() as logs:
            result = await Dummy()({})

        assert result == {"result": "ok", "result_failed": False}
        events = [log["event"] for log in logs]
        assert events == ["node_started", "node_finished"]

        finished = logs[1]
        assert finished["node"] == "dummy_node"
        assert set(finished["output_keys"]) == {"result", "result_failed"}
        assert finished["failed"] is False

    async def test_logs_failed_true_when_output_flag_is_set(self) -> None:
        with structlog.testing.capture_logs() as logs:
            await Dummy()({"should_fail": True})

        finished = logs[1]
        assert finished["failed"] is True

    async def test_logs_node_failed_on_exception_and_reraises(self) -> None:
        with structlog.testing.capture_logs() as logs:
            with pytest.raises(ValueError, match="kaboom"):
                await Dummy()({"boom": True})

        events = [log["event"] for log in logs]
        assert events == ["node_started", "node_failed"]
        assert logs[1]["log_level"] == "error"
