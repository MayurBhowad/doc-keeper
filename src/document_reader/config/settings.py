import os

class Settings:

    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv(
            "OPENAI_MODEL",
            "gpt-5.6-mini",
        )