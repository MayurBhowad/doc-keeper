from dataclasses import dataclass
from typing import Any

from document_reader.domain.schema import ExtractionSchema


@dataclass(frozen=True)
class ExtractionRequest:
    query: str
    schema: type[ExtractionSchema] | None = None


@dataclass(frozen=True)
class ExtractionResult:
    data: dict[str, Any]