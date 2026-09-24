from abc import ABC, abstractmethod

from document_reader.domain.content import DocumentContent
from document_reader.domain.extraction import ExtractionRequest, ExtractionResult

class DocumentExtractor(ABC):

    @abstractmethod
    def extract(self, content: DocumentContent, request: ExtractionRequest) -> ExtractionResult:
        pass