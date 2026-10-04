class ExtractionValidationError(ValueError):
    """Raised when an extraction result does not match the requested schema."""


class ExtractionParsingError(ValueError):
    """Raised when an LLM response cannot be parsed as structured data."""