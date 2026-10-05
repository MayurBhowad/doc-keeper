from typing import Any

import pytest

from document_reader.domain.content import DocumentContent
from document_reader.domain.extraction import ExtractionRequest
from document_reader.domain.validation import (
    ExtractionParsingError,
    ExtractionValidationError,
)
from document_reader.extractors.llm import LLMExtractor

from document_reader.domain.schema import ExtractionSchema

class InvoiceExtraction(ExtractionSchema):
    invoice_number: str
    vendor_name: str
    total: float


class FakeLLMClient:

    def __init__(self):
        self.last_prompt = None

    def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        return """
            {
                "invoice_number": "INV-123",
                "vendor_name": "ABC Pvt Ltd",
                "total": 15000
            }
            """

    
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
        schema=InvoiceExtraction,
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

    assert '"type": "string"' in client.last_prompt
    assert '"type": "number"' in client.last_prompt


def test_llm_extractor_rejects_invalid_schema_result():
    class InvalidFakeLLMClient(FakeLLMClient):

        def generate(self, prompt: str) -> str:
            self.last_prompt = prompt
            return """
                {
                    "invoice_number": "INV-123",
                    "vendor_name": "ABC Pvt Ltd",
                    "total": "15000"
                }
                """

    client = InvalidFakeLLMClient()

    extractor = LLMExtractor(client)

    content = DocumentContent(
        filename="invoice.pdf",
        document_type="pdf",
        text="Invoice INV-123 ABC Pvt Ltd Total 15000",
    )

    request = ExtractionRequest(
        query="Extract invoice details",
        schema=InvoiceExtraction,
    )

    with pytest.raises(
        ExtractionValidationError,
        match="valid number",
    ):
        extractor.extract(content, request)


def test_llm_extractor_rejects_missing_schema_field():
    class MissingFieldFakeLLMClient(FakeLLMClient):

        def generate(self, prompt: str) -> str:
            self.last_prompt = prompt

            return """
            {
                "invoice_number": "INV-123",
                "vendor_name": "ABC Pvt Ltd"
            }
            """

    client = MissingFieldFakeLLMClient()

    extractor = LLMExtractor(client)

    content = DocumentContent(
        filename="invoice.pdf",
        document_type="pdf",
        text="Invoice INV-123 ABC Pvt Ltd Total 15000",
    )

    request = ExtractionRequest(
        query="Extract invoice details",
        schema=InvoiceExtraction,
    )

    with pytest.raises(
        ExtractionValidationError,
        match="Field required",
    ):
        extractor.extract(content, request)


def test_llm_extractor_parses_json_code_fence():
    class CodeFenceFakeLLMClient(FakeLLMClient):

        def generate(self, prompt: str) -> str:
            self.last_prompt = prompt

            return """
            ```json
            {
                "invoice_number": "INV-123",
                "vendor_name": "ABC Pvt Ltd",
                "total": 15000
            }
            ```
            """

    client = CodeFenceFakeLLMClient()
    extractor = LLMExtractor(client)

    content = DocumentContent(
        filename="invoice.pdf",
        document_type="pdf",
        text="Invoice INV-123 ABC Pvt Ltd Total 15000",
    )

    request = ExtractionRequest(
        query="Extract invoice details",
    )

    result = extractor.extract(content, request)

    assert result.data["invoice_number"] == "INV-123"
    assert result.data["vendor_name"] == "ABC Pvt Ltd"
    assert result.data["total"] == 15000


def test_llm_extractor_parses_plain_code_fence():
    class CodeFenceFakeLLMClient(FakeLLMClient):

        def generate(self, prompt: str) -> str:
            self.last_prompt = prompt

            return """
            ```
            {
                "invoice_number": "INV-123",
                "vendor_name": "ABC Pvt Ltd",
                "total": 15000
            }
            ```
            """

    client = CodeFenceFakeLLMClient()
    extractor = LLMExtractor(client)

    content = DocumentContent(
        filename="invoice.pdf",
        document_type="pdf",
        text="Invoice INV-123 ABC Pvt Ltd Total 15000",
    )

    request = ExtractionRequest(
        query="Extract invoice details",
    )

    result = extractor.extract(content, request)

    assert result.data["invoice_number"] == "INV-123"
    assert result.data["vendor_name"] == "ABC Pvt Ltd"
    assert result.data["total"] == 15000


def test_llm_extractor_rejects_invalid_json_in_code_fence():
    class InvalidCodeFenceFakeLLMClient(FakeLLMClient):

        def generate(self, prompt: str) -> str:
            self.last_prompt = prompt

            return """
            ```json
            {
                "invoice_number": "INV-123",
                "vendor_name": "ABC Pvt Ltd",
                "total": 15000,
            }
            ```
            """

    client = InvalidCodeFenceFakeLLMClient()
    extractor = LLMExtractor(client)

    content = DocumentContent(
        filename="invoice.pdf",
        document_type="pdf",
        text="Invoice INV-123 ABC Pvt Ltd Total 15000",
    )

    request = ExtractionRequest(
        query="Extract invoice details",
    )

    with pytest.raises(
        ExtractionParsingError,
        match="LLM response is not valid JSON",
    ):
        extractor.extract(content, request)


def test_llm_extractor_validates_code_fenced_response_with_schema():
    class CodeFenceSchemaFakeLLMClient(FakeLLMClient):

        def generate(self, prompt: str) -> str:
            self.last_prompt = prompt

            return """
            ```json
            {
                "invoice_number": "INV-123",
                "vendor_name": "ABC Pvt Ltd",
                "total": 15000
            }
            ```
            """

    client = CodeFenceSchemaFakeLLMClient()
    extractor = LLMExtractor(client)

    content = DocumentContent(
        filename="invoice.pdf",
        document_type="pdf",
        text="Invoice INV-123 ABC Pvt Ltd Total 15000",
    )

    request = ExtractionRequest(
        query="Extract invoice details",
        schema=InvoiceExtraction,
    )

    result = extractor.extract(content, request)

    assert result.data == {
        "invoice_number": "INV-123",
        "vendor_name": "ABC Pvt Ltd",
        "total": 15000,
    }


def test_llm_extractor_preserves_plain_json_response():
    client = FakeLLMClient()
    extractor = LLMExtractor(client)

    content = DocumentContent(
        filename="invoice.pdf",
        document_type="pdf",
        text="Invoice INV-123 ABC Pvt Ltd Total 15000",
    )

    request = ExtractionRequest(
        query="Extract invoice details",
    )

    result = extractor.extract(content, request)

    assert result.data == {
        "invoice_number": "INV-123",
        "vendor_name": "ABC Pvt Ltd",
        "total": 15000,
    }

def test_llm_extractor_parses_json_with_surrounding_text():
    class SurroundingTextFakeLLMClient(FakeLLMClient):

        def generate(self, prompt: str) -> str:
            self.last_prompt = prompt

            return """
            Here is the extracted invoice information:

            {
                "invoice_number": "INV-123",
                "vendor_name": "ABC Pvt Ltd",
                "total": 15000
            }

            I hope this helps.
            """

    client = SurroundingTextFakeLLMClient()
    extractor = LLMExtractor(client)

    content = DocumentContent(
        filename="invoice.pdf",
        document_type="pdf",
        text="Invoice INV-123 ABC Pvt Ltd Total 15000",
    )

    request = ExtractionRequest(
        query="Extract invoice details",
    )

    result = extractor.extract(content, request)

    assert result.data == {
        "invoice_number": "INV-123",
        "vendor_name": "ABC Pvt Ltd",
        "total": 15000,
    }

def test_llm_extractor_parses_nested_json_with_surrounding_text():
    class NestedJSONFakeLLMClient(FakeLLMClient):

        def generate(self, prompt: str) -> str:
            self.last_prompt = prompt

            return """
            Here is the extracted invoice information:

            {
                "invoice_number": "INV-123",
                "vendor": {
                    "name": "ABC Pvt Ltd",
                    "address": {
                        "city": "Mumbai"
                    }
                },
                "total": 15000
            }

            I hope this helps.
            """

    client = NestedJSONFakeLLMClient()
    extractor = LLMExtractor(client)

    content = DocumentContent(
        filename="invoice.pdf",
        document_type="pdf",
        text="Invoice INV-123 ABC Pvt Ltd Total 15000",
    )

    request = ExtractionRequest(
        query="Extract invoice details",
    )

    result = extractor.extract(content, request)

    assert result.data["invoice_number"] == "INV-123"
    assert result.data["vendor"]["name"] == "ABC Pvt Ltd"
    assert result.data["vendor"]["address"]["city"] == "Mumbai"
    assert result.data["total"] == 15000



def test_llm_extractor_parses_code_fenced_json_with_surrounding_text():
    class CodeFenceSurroundingTextFakeLLMClient(FakeLLMClient):

        def generate(self, prompt: str) -> str:
            self.last_prompt = prompt

            return """
            Here is the extracted invoice information:

            ```json
            {
                "invoice_number": "INV-123",
                "vendor_name": "ABC Pvt Ltd",
                "total": 15000
            }
            ```

            I hope this helps.
            """

    client = CodeFenceSurroundingTextFakeLLMClient()
    extractor = LLMExtractor(client)

    content = DocumentContent(
        filename="invoice.pdf",
        document_type="pdf",
        text="Invoice INV-123 ABC Pvt Ltd Total 15000",
    )

    request = ExtractionRequest(
        query="Extract invoice details",
    )

    result = extractor.extract(content, request)

    assert result.data == {
        "invoice_number": "INV-123",
        "vendor_name": "ABC Pvt Ltd",
        "total": 15000,
    }


def test_llm_extractor_rejects_surrounding_text_without_json():
    class InvalidSurroundingTextFakeLLMClient(FakeLLMClient):

        def generate(self, prompt: str) -> str:
            self.last_prompt = prompt

            return """
            Here is the extracted invoice information.

            Unfortunately, no structured result is available.
            """

    client = InvalidSurroundingTextFakeLLMClient()
    extractor = LLMExtractor(client)

    content = DocumentContent(
        filename="invoice.pdf",
        document_type="pdf",
        text="Invoice INV-123 ABC Pvt Ltd Total 15000",
    )

    request = ExtractionRequest(
        query="Extract invoice details",
    )

    with pytest.raises(
        ExtractionParsingError,
        match="does not contain a JSON object",
    ):
        extractor.extract(content, request)

def test_llm_extractor_parses_json_with_text_after_it():
    class TrailingTextFakeLLMClient(FakeLLMClient):

        def generate(self, prompt: str) -> str:
            self.last_prompt = prompt

            return """
            {
                "invoice_number": "INV-123",
                "vendor_name": "ABC Pvt Ltd",
                "total": 15000
            }

            This is additional explanatory information.
            """

    client = TrailingTextFakeLLMClient()
    extractor = LLMExtractor(client)

    content = DocumentContent(
        filename="invoice.pdf",
        document_type="pdf",
        text="Invoice INV-123 ABC Pvt Ltd Total 15000",
    )

    request = ExtractionRequest(
        query="Extract invoice details",
    )

    result = extractor.extract(content, request)

    assert result.data == {
        "invoice_number": "INV-123",
        "vendor_name": "ABC Pvt Ltd",
        "total": 15000,
    }