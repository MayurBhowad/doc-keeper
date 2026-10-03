from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ExtractionRequest:
    query: str
    schema: dict[str, str] | None = None


@dataclass(frozen=True)
class ExtractionResult:
    data: dict[str, Any]