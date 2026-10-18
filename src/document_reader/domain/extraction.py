from dataclasses import dataclass, field
from math import isfinite
from typing import Any

from document_reader.domain.schema import ExtractionSchema


@dataclass(frozen=True)
class ExtractionRequest:
    query: str
    schema: type[ExtractionSchema] | None = None


@dataclass(frozen=True)
class FieldMetadata:
    confidence: float | None = None
    source_pages: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        if self.confidence is not None:
            if (
                isinstance(self.confidence, bool)
                or not isinstance(self.confidence, (int, float))
                or not isfinite(self.confidence)
                or not 0.0 <= self.confidence <= 1.0
            ):
                raise ValueError("confidence must be between 0.0 and 1.0")

        if any(
            isinstance(page, bool)
            or not isinstance(page, int)
            or page < 1
            for page in self.source_pages
        ):
            raise ValueError("source_pages must contain positive page numbers")

    def is_low_confidence(self, threshold: float = 0.5) -> bool:
        if (
            isinstance(threshold, bool)
            or not isinstance(threshold, (int, float))
            or not isfinite(threshold)
            or not 0.0 <= threshold <= 1.0
        ):
            raise ValueError("threshold must be between 0.0 and 1.0")

        return (
            self.confidence is not None
            and self.confidence < threshold
        )


@dataclass(frozen=True)
class ExtractionResult:
    data: dict[str, Any]
    metadata: dict[str, Any] | None = None
    field_metadata: dict[str, FieldMetadata] = field(default_factory=dict)
