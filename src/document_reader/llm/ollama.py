
import httpx

from document_reader.config.settings import Settings
from document_reader.llm.base import LLMClient


class OllamaClient(LLMClient):
    def __init__(self, settings: Settings):
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model

    def generate(self, prompt: str) -> str:
        response = httpx.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=300.0,
        )
        response.raise_for_status()
        data = response.json()
        return data["response"]
