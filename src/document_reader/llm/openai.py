import json
from openai import OpenAI
from document_reader.config.settings import Settings
from document_reader.llm.base import LLMClient


class OpenAIClient(LLMClient):
    def __init__(self, settings: Settings):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    def generate(self, prompt: str) -> dict:
        response = self.client.responses.create(
            model=self.model,
            input=prompt,
        )

        return json.loads(response.output_text)