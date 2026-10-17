import json
import time
from typing import Any

from document_reader.domain.content import DocumentContent
from document_reader.domain.extraction import ExtractionRequest, ExtractionResult, FieldMetadata
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
        start_time = time.perf_counter()
        prompt = self._build_prompt(content, request)

        last_error = None
        current_prompt = prompt

        for attempt in range(self.max_attempts):
            response = self.client.generate(current_prompt)

            try:
                data, field_metadata = self._parse_extraction_response(response)

                if request.schema:
                    data = self.validator.validate(data, request.schema)

                duration_ms = int(
                    (time.perf_counter() - start_time) * 1000
                )

                return ExtractionResult(
                    data=data,
                    metadata={
                        "attempts": attempt + 1,
                        "duration_ms": duration_ms,
                        "model": self.client.model,
                    },
                    field_metadata=field_metadata,
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
            schema_json = json.dumps(
                request.schema.model_json_schema(),
                indent=2,
            )
            schema_instruction = f"""
Expected response schema:
{schema_json}

The "data" object must contain exactly the fields defined in this schema.
""".strip()

        if content.pages:
            document_text = "\n\n".join(
                f"Page {page_number}:\n{page_text}"
                for page_number, page_text in enumerate(
                    content.pages,
                    start=1,
                )
            )
        else:
            document_text = content.text

        return f"""
You are a document extraction assistant.

Document:
{document_text}

User request:
{request.query}

{schema_instruction}

Extract the requested information from the document.

For each extracted field, provide optional metadata:
- confidence: an estimate between 0.0 and 1.0 based on document evidence.
  This is not a calibrated probability.
- source_pages: a list of 1-based page numbers supporting the value.
- Do not invent page numbers or evidence.

Return only a JSON object in this format:
{{
  "data": {{
    "field_name": "extracted value"
  }},
  "field_metadata": {{
    "field_name": {{
      "confidence": 0.9,
      "source_pages": [1]
    }}
  }}
}}

Include metadata where possible. If metadata is unavailable, omit it
rather than inventing it.
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

    def _parse_extraction_response(
        self,
        response: str,
    ) -> tuple[dict[str, Any], dict[str, FieldMetadata]]:
        parsed = self._parse_response(response)

        # Preserve compatibility with legacy plain-JSON responses.
        if "data" not in parsed:
            return parsed, {}

        data = parsed["data"]
        raw_metadata = parsed.get("field_metadata", {})

        if not isinstance(data, dict):
            raise ExtractionParsingError(
                "The 'data' property must be a JSON object."
            )

        if not isinstance(raw_metadata, dict):
            raise ExtractionParsingError(
                "The 'field_metadata' property must be a JSON object."
            )

        field_metadata: dict[str, FieldMetadata] = {}

        try:
            for field_name, values in raw_metadata.items():
                if field_name not in data:
                    raise ValueError(
                        f"Metadata references unknown field '{field_name}'."
                    )

                if not isinstance(values, dict):
                    raise ValueError(
                        "Each field metadata entry must be an object keyed by field name."
                    )

                confidence = values.get("confidence")
                source_pages = values.get("source_pages", [])

                if not isinstance(source_pages, list):
                    raise ValueError(
                        f"source_pages for '{field_name}' must be a list."
                    )

                field_metadata[field_name] = FieldMetadata(
                    confidence=confidence,
                    source_pages=tuple(source_pages),
                )
        except (TypeError, ValueError) as exc:
            raise ExtractionParsingError(
                f"Invalid field metadata: {exc}"
            ) from exc

        return data, field_metadata
