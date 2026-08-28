import pytest

from app.adapters.llm_factory import build_llm_client
from app.adapters.ollama_llm import OllamaClient
from app.adapters.openai_llm import OpenAIClient


class TestBuildLlmClient:
    def test_defaults_to_ollama_when_no_openai_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("OLLAMA_MODEL", raising=False)
        monkeypatch.delenv("OLLAMA_HOST", raising=False)

        client = build_llm_client()

        assert isinstance(client, OllamaClient)

    def test_treats_empty_openai_key_as_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OPENAI_API_KEY", "")

        client = build_llm_client()

        assert isinstance(client, OllamaClient)

    def test_uses_openai_when_key_is_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-123")
        monkeypatch.delenv("OPENAI_MODEL", raising=False)

        client = build_llm_client()

        assert isinstance(client, OpenAIClient)

    def test_respects_ollama_model_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("OLLAMA_MODEL", "llama3.2:3b")

        client = build_llm_client()

        assert isinstance(client, OllamaClient)
        assert client._model == "llama3.2:3b"

    def test_respects_openai_model_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-123")
        monkeypatch.setenv("OPENAI_MODEL", "gpt-5-nano")

        client = build_llm_client()

        assert isinstance(client, OpenAIClient)
        assert client._model == "gpt-5-nano"
