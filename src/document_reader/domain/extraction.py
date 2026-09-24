from dataclasses import dataclass


@dataclass(frozen=True)
class ExtractionRequest:
    query: str

@dataclass(frozen=True)
class ExtractionResult:
    data: dict