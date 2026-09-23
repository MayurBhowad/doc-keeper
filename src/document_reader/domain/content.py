from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentContent:
    filename: str
    document_type: str
    text: str