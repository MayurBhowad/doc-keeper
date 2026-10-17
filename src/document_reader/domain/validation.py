from typing import Any


class ExtractionValidationError(ValueError):
    """Raised when an extraction result does not match the requested schema."""

    def __init__(
        self,
        message: str,
        issues: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.issues = issues or []


class ExtractionParsingError(ValueError):
    """Raised when an LLM response cannot be parsed as structured data."""