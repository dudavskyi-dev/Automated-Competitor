import os

from app.adapters.ollama_llm import DEFAULT_HOST as OLLAMA_DEFAULT_HOST
from app.adapters.ollama_llm import DEFAULT_MODEL as OLLAMA_DEFAULT_MODEL
from app.adapters.ollama_llm import OllamaClient
from app.adapters.openai_llm import DEFAULT_MODEL as OPENAI_DEFAULT_MODEL
from app.adapters.openai_llm import OpenAIClient
from app.ports.llm import LLMClient


def build_llm_client() -> LLMClient:
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        model = os.environ.get("OPENAI_MODEL", OPENAI_DEFAULT_MODEL)
        return OpenAIClient(api_key=api_key, model=model)
    model = os.environ.get("OLLAMA_MODEL", OLLAMA_DEFAULT_MODEL)
    host = os.environ.get("OLLAMA_HOST", OLLAMA_DEFAULT_HOST)
    return OllamaClient(model=model, host=host)
