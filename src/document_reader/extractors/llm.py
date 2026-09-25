from document_reader.domain.content import DocumentContent
from document_reader.domain.extraction import ExtractionRequest, ExtractionResult
from document_reader.extractors.base import DocumentExtractor
from document_reader.llm.base import LLMClient


class LLMExtractor(DocumentExtractor):

    def __init__(self, client: LLMClient):
        self.client = client

    def extract(self, content: DocumentContent, request: ExtractionRequest) -> ExtractionResult:
        prompt = self._build_prompt(content, request)

        response = self.client.generate(prompt)

        return ExtractionResult(data=response)

    def _build_prompt(self, content: DocumentContent, request: ExtractionRequest) -> str:
        return f"""
        You are a document extraction assistant.

        Document:
        {content.text}

        User request:
        {request.query}

        Extract the requested information from the document.
        Return only the extracted result.
        """.strip()