from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ExtractionRequest:
    query: str

@dataclass(frozen=True)
class ExtractionResult:
    data: dict[str, Any]