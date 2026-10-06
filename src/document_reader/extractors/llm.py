import json
from typing import Any

from document_reader.domain.content import DocumentContent
from document_reader.domain.extraction import ExtractionRequest, ExtractionResult
from document_reader.domain.validation import (
    ExtractionParsingError,
    ExtractionValidationError,
)
from document_reader.domain.validator import ExtractionValidator
from document_reader.extractors.base import DocumentExtractor
from document_reader.llm.base import LLMClient


class LLMExtractor(DocumentExtractor):

    def __init__(
        self,
        client: LLMClient,
        validator: ExtractionValidator | None = None,
        max_attempts: int = 2,
    ):
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")

        self.client = client
        self.validator = validator or ExtractionValidator()
        self.max_attempts = max_attempts

    def extract(
        self,
        content: DocumentContent,
        request: ExtractionRequest,
    ) -> ExtractionResult:
        prompt = self._build_prompt(content, request)

        last_error = None
        current_prompt = prompt

        for attempt in range(self.max_attempts):
            response = self.client.generate(current_prompt)

            try:
                data = self._parse_response(response)

                if request.schema:
                    data = self.validator.validate(data, request.schema)

                return ExtractionResult(
                    data=data,
                    metadata={
                        "attempts": attempt + 1,
                    },
                )

            except (ExtractionParsingError, ExtractionValidationError) as exc:
                last_error = exc

                if attempt < self.max_attempts - 1:
                    current_prompt = (
                        f"{prompt}\n\n"
                        "Previous response failed extraction validation.\n\n"
                        f"Error:\n{exc}\n\n"
                        "Please correct the response and return only the extracted result."
                    )

        if last_error:
            raise last_error

        raise ExtractionParsingError(
            "LLM extraction failed after maximum attempts."
        )

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

    def _parse_response(
        self,
        response: str,
    ) -> dict[str, Any]:
        response = response.strip()

        if response.startswith("```json") and response.endswith("```"):
            response = response[7:-3].strip()
        elif response.startswith("```") and response.endswith("```"):
            response = response[3:-3].strip()

        decoder = json.JSONDecoder()

        try:
            start = response.find("{")

            if start == -1:
                raise ExtractionParsingError(
                    "LLM response does not contain a JSON object."
                )

            data, _ = decoder.raw_decode(response[start:])
        except json.JSONDecodeError as exc:
            raise ExtractionParsingError(
                "LLM response is not valid JSON."
            ) from exc

        if not isinstance(data, dict):
            raise ExtractionParsingError(
                "LLM response must be a JSON object."
            )

        return data
