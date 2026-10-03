from typing import Any

import pytest

from document_reader.domain.content import DocumentContent
from document_reader.domain.extraction import ExtractionRequest
from document_reader.domain.validation import ExtractionValidationError
from document_reader.extractors.llm import LLMExtractor


class FakeLLMClient:

    def __init__(self):
        self.last_prompt = None

    def generate(self, prompt: str) -> dict[str, Any]:
        self.last_prompt = prompt
        return {
            "invoice_number": "INV-123",
            "vendor_name": "ABC Pvt Ltd",
            "total": 15000,
        }

    
def test_llm_extractor():
    client = FakeLLMClient()

    extractor = LLMExtractor(client)

    content = DocumentContent(
        filename="invoice.pdf",
        document_type="pdf",
        text="Invoice INV-123 ABC Pvt Ltd Total 15000",
    )

    request = ExtractionRequest(
        query="Give me invoice number, vendor and total"
    )

    result = extractor.extract(content, request)

    assert "Invoice INV-123 ABC Pvt Ltd Total 15000" in client.last_prompt
    assert "Give me invoice number, vendor and total" in client.last_prompt

    assert result.data["invoice_number"] == "INV-123"
    assert result.data["vendor_name"] == "ABC Pvt Ltd"
    assert result.data["total"] == 15000
    assert "Expected response schema:" not in client.last_prompt


def test_llm_extractor_with_schema():
    client = FakeLLMClient()

    extractor = LLMExtractor(client)

    content = DocumentContent(
        filename="invoice.pdf",
        document_type="pdf",
        text="Invoice INV-123 ABC Pvt Ltd Total 15000",
    )

    request = ExtractionRequest(
        query="Extract invoice details",
        schema={
            "invoice_number": "string",
            "vendor_name": "string",
            "total": "number",
        },
    )

    result = extractor.extract(content, request)

    assert "Extract invoice details" in client.last_prompt
    assert "invoice_number" in client.last_prompt
    assert "vendor_name" in client.last_prompt
    assert "total" in client.last_prompt
    assert "string" in client.last_prompt
    assert "number" in client.last_prompt

    assert result.data["invoice_number"] == "INV-123"
    assert result.data["vendor_name"] == "ABC Pvt Ltd"
    assert result.data["total"] == 15000


def test_llm_extractor_rejects_invalid_schema_result():
    class InvalidFakeLLMClient(FakeLLMClient):

        def generate(self, prompt: str) -> dict[str, Any]:
            self.last_prompt = prompt
            return {
                "invoice_number": "INV-123",
                "vendor_name": "ABC Pvt Ltd",
                "total": "15000",
            }

    client = InvalidFakeLLMClient()

    extractor = LLMExtractor(client)

    content = DocumentContent(
        filename="invoice.pdf",
        document_type="pdf",
        text="Invoice INV-123 ABC Pvt Ltd Total 15000",
    )

    request = ExtractionRequest(
        query="Extract invoice details",
        schema={
            "invoice_number": "string",
            "vendor_name": "string",
            "total": "number",
        },
    )

    with pytest.raises(
        ExtractionValidationError,
        match="Field 'total' expected number but received string",
    ):
        extractor.extract(content, request)


def test_llm_extractor_rejects_missing_schema_field():
    class MissingFieldFakeLLMClient(FakeLLMClient):

        def generate(self, prompt: str) -> dict[str, Any]:
            self.last_prompt = prompt
            return {
                "invoice_number": "INV-123",
                "vendor_name": "ABC Pvt Ltd",
            }

    client = MissingFieldFakeLLMClient()

    extractor = LLMExtractor(client)

    content = DocumentContent(
        filename="invoice.pdf",
        document_type="pdf",
        text="Invoice INV-123 ABC Pvt Ltd Total 15000",
    )

    request = ExtractionRequest(
        query="Extract invoice details",
        schema={
            "invoice_number": "string",
            "vendor_name": "string",
            "total": "number",
        },
    )

    with pytest.raises(
        ExtractionValidationError,
        match="Missing required field 'total'",
    ):
        extractor.extract(content, request)
