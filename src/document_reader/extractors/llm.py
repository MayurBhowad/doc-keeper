import json
from document_reader.domain.content import DocumentContent
from document_reader.domain.extraction import ExtractionRequest, ExtractionResult
from document_reader.domain.validator import ExtractionValidator
from document_reader.extractors.base import DocumentExtractor
from document_reader.llm.base import LLMClient


class LLMExtractor(DocumentExtractor):

    def __init__(
        self,
        client: LLMClient,
        validator: ExtractionValidator | None = None,
    ):
        self.client = client
        self.validator = validator or ExtractionValidator()

    def extract(
        self,
        content: DocumentContent,
        request: ExtractionRequest,
    ) -> ExtractionResult:
        prompt = self._build_prompt(content, request)

        response = self.client.generate(prompt)

        if request.schema:
            response = self.validator.validate(response, request.schema)

        return ExtractionResult(data=response)

    def _build_prompt(
        self,
        content: DocumentContent,
        request: ExtractionRequest,
    ) -> str:
        schema_instruction = ""

        if request.schema:
            schema = request.schema.model_json_schema()
            schema_json = json.dumps(schema, indent=2)

            schema_instruction = f"""
            Expected response schema:
            {schema_json}

            Return the extracted data using exactly the fields defined
            in the schema.
            """.strip()

        return f"""
        You are a document extraction assistant.

        Document:
        {content.text}

        User request:
        {request.query}

        {schema_instruction}

        Extract the requested information from the document.
        Return only the extracted result.
        """.strip()
