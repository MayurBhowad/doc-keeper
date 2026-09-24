from pathlib import Path

from document_reader.domain.extraction import ExtractionRequest
from document_reader.extractors.fake import FakeExtractor

from .domain.document import Document
from .readers.registry import ReaderRegistry
from .storage.json import JsonStorage


class DocumentEngine:

    def __init__(
        self,
        reader_registry=None,
        extractor=None,
        storage=None,
    ):
        self.reader_registry = (
            reader_registry or ReaderRegistry()
        )
        self.extractor = extractor or FakeExtractor()
        self.storage = (
            storage or JsonStorage()
        )

    def process(self, path: str, query: str):
        document = Document(
            path=Path(path)
        )

        reader = self.reader_registry.get(
            document.extension
        )

        content = reader.read(document)

        request = ExtractionRequest(query=query)

        result = self.extractor.extract(content, request)

        output_path = self.storage.save(content.filename, result)

        return {
            "filename": content.filename,
            "data": result.data,
            "output": str(output_path),
        }