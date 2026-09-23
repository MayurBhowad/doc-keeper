from pathlib import Path

from .domain.document import Document
from .readers.registry import ReaderRegistry
from .storage.json import JsonStorage


class DocumentEngine:

    def __init__(
        self,
        reader_registry=None,
        storage=None,
    ):
        self.reader_registry = (
            reader_registry or ReaderRegistry()
        )
        self.storage = (
            storage or JsonStorage()
        )

    def process(self, path: str):
        document = Document(
            path=Path(path)
        )

        reader = self.reader_registry.get(
            document.extension
        )

        content = reader.read(document)

        output_path = self.storage.save(content)

        return {
            "filename": content.filename,
            "content": content.text,
            "output": str(output_path),
        }