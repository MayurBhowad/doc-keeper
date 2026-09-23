from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Document:
    path: Path

    @property
    def filename(self) -> str:
        return self.path.name

    @property
    def extension(self) -> str:
        return self.path.suffix.lower()