from pathlib import Path

from document_reader.domain.extraction import ExtractionRequest
from document_reader.domain.schema import ExtractionSchema
from document_reader.domain.validator import BusinessValidator
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
        business_validator: BusinessValidator | None = None,
    ):
        self.reader_registry = (
            reader_registry or ReaderRegistry()
        )
        self.extractor = extractor or FakeExtractor()
        self.storage = (
            storage or JsonStorage()
        )
        self.business_validator = business_validator

    def process(
        self,
        path: str,
        query: str,
        schema: type[ExtractionSchema] | None = None,
        output_filename: str | None = None,
    ):
        document = Document(
            path=Path(path)
        )

        reader = self.reader_registry.get(
            document.extension
        )

        content = reader.read(document)

        request = ExtractionRequest(query=query, schema=schema)

        result = self.extractor.extract(content, request)

        if self.business_validator is not None:
            self.business_validator.validate(
                result.data,
                raise_on_error=True,
            )

        output_path = self.storage.save(
            output_filename or content.filename,
            result,
        )

        response = {
            "filename": content.filename,
            "data": result.data,
            "output": str(output_path),
        }

        if result.metadata is not None:
            response["metadata"] = result.metadata

        if result.field_metadata:
            response["field_metadata"] = {
                name: {
                    "confidence": metadata.confidence,
                    "source_pages": list(metadata.source_pages),
                }
                for name, metadata in result.field_metadata.items()
            }

        return response
