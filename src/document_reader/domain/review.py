from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from document_reader.domain.extraction import ExtractionResult


class ReviewStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class ReviewRecord:
    extraction: ExtractionResult
    status: ReviewStatus = ReviewStatus.PENDING
    corrected_data: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.extraction, ExtractionResult):
            raise TypeError("extraction must be an ExtractionResult")

        if not isinstance(self.status, ReviewStatus):
            raise ValueError("status must be a ReviewStatus")

        if not isinstance(self.corrected_data, dict):
            raise TypeError("corrected_data must be a dictionary")

        unknown_fields = self.corrected_data.keys() - self.extraction.data.keys()
        if unknown_fields:
            raise ValueError(
                f"Unknown corrected fields: {sorted(unknown_fields)}"
            )

    @property
    def effective_data(self) -> dict[str, Any]:
        return {**self.extraction.data, **self.corrected_data}

    def correct_field(self, field_name: str, value: Any) -> None:
        self._ensure_pending()

        if field_name not in self.extraction.data:
            raise ValueError(f"Unknown field: {field_name}")

        self.corrected_data[field_name] = value

    def approve(self) -> None:
        self._ensure_pending()
        self.status = ReviewStatus.APPROVED

    def reject(self) -> None:
        self._ensure_pending()
        self.status = ReviewStatus.REJECTED

    def _ensure_pending(self) -> None:
        if self.status is not ReviewStatus.PENDING:
            raise ValueError(
                f"Cannot modify a review with status '{self.status.value}'"
            )
