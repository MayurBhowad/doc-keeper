from document_reader.domain.content import DocumentContent
from document_reader.domain.extraction import ExtractionRequest, ExtractionResult
from document_reader.extractors.base import DocumentExtractor


class FakeExtractor(DocumentExtractor):

    def extract(self, content: DocumentContent, request: ExtractionRequest) -> ExtractionResult:
        return ExtractionResult(data={"query": request.query, "filename": content.filename, "text": content.text})