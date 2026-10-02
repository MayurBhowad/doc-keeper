from abc import ABC, abstractmethod
from typing import Any


class LLMClient(ABC):

    @abstractmethod
    def generate(self, prompt: str) -> dict[str, Any]:
        pass
