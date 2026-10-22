import os


class Settings:
    def __init__(self):
        self.llm_provider = os.getenv("LLM_PROVIDER", "openai").lower()

        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-5.6-mini")

        self.ollama_base_url = os.getenv(
            "OLLAMA_BASE_URL",
            "http://localhost:11434",
        )
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3:latest")