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
    model = "test-model"

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


def test_llm_extractor_retries_after_validation_failure():
    class RetryFakeLLMClient:
        model = "test-model"
        def __init__(self):
            self.call_count = 0
            self.prompts = []

        def generate(self, prompt: str) -> str:
            self.call_count += 1
            self.prompts.append(prompt)

            if self.call_count == 1:
                return """
                {
                    "invoice_number": "INV-123",
                    "vendor_name": "ABC Pvt Ltd",
                    "total": "invalid"
                }
                """

            return """
            {
                "invoice_number": "INV-123",
                "vendor_name": "ABC Pvt Ltd",
                "total": 15000
            }
            """

    client = RetryFakeLLMClient()
    extractor = LLMExtractor(client, max_attempts=2)

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

    assert client.call_count == 2
    assert result.data["invoice_number"] == "INV-123"
    assert result.data["vendor_name"] == "ABC Pvt Ltd"
    assert result.data["total"] == 15000


def test_llm_extractor_retries_after_parsing_failure():
    class RetryFakeLLMClient:
        model = "test-model"
        def __init__(self):
            self.call_count = 0

        def generate(self, prompt: str) -> str:
            self.call_count += 1

            if self.call_count == 1:
                return "This is not valid JSON."

            return """
            {
                "invoice_number": "INV-123",
                "vendor_name": "ABC Pvt Ltd",
                "total": 15000
            }
            """

    client = RetryFakeLLMClient()
    extractor = LLMExtractor(client, max_attempts=2)

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

    assert client.call_count == 2
    assert result.data["invoice_number"] == "INV-123"
    assert result.data["vendor_name"] == "ABC Pvt Ltd"
    assert result.data["total"] == 15000


def test_llm_extractor_respects_max_attempts():
    class AlwaysFailingLLMClient:
        def __init__(self):
            self.call_count = 0

        def generate(self, prompt: str) -> str:
            self.call_count += 1
            return "This is not valid JSON."

    client = AlwaysFailingLLMClient()
    extractor = LLMExtractor(client, max_attempts=3)

    content = DocumentContent(
        filename="invoice.pdf",
        document_type="pdf",
        text="Invoice INV-123 ABC Pvt Ltd Total 15000",
    )

    request = ExtractionRequest(
        query="Extract invoice details",
        schema=InvoiceExtraction,
    )

    with pytest.raises(ExtractionParsingError):
        extractor.extract(content, request)

    assert client.call_count == 3


def test_llm_extractor_preserves_final_validation_error():
    class AlwaysInvalidLLMClient:
        def __init__(self):
            self.call_count = 0

        def generate(self, prompt: str) -> str:
            self.call_count += 1

            return """
            {
                "invoice_number": "INV-123",
                "vendor_name": "ABC Pvt Ltd",
                "total": "invalid"
            }
            """

    client = AlwaysInvalidLLMClient()
    extractor = LLMExtractor(client, max_attempts=2)

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

    assert client.call_count == 2


def test_llm_extractor_preserves_final_parsing_error():
    class AlwaysInvalidJSONClient:
        def __init__(self):
            self.call_count = 0

        def generate(self, prompt: str) -> str:
            self.call_count += 1
            return "This is not valid JSON."

    client = AlwaysInvalidJSONClient()
    extractor = LLMExtractor(client, max_attempts=2)

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
        ExtractionParsingError,
        match="does not contain a JSON object",
    ):
        extractor.extract(content, request)

    assert client.call_count == 2


def test_llm_extractor_includes_failure_in_retry_prompt():
    class RetryFakeLLMClient:
        model = "test-model"
        def __init__(self):
            self.call_count = 0
            self.prompts = []

        def generate(self, prompt: str) -> str:
            self.call_count += 1
            self.prompts.append(prompt)

            if self.call_count == 1:
                return """
                {
                    "invoice_number": "INV-123",
                    "vendor_name": "ABC Pvt Ltd",
                    "total": "invalid"
                }
                """

            return """
            {
                "invoice_number": "INV-123",
                "vendor_name": "ABC Pvt Ltd",
                "total": 15000
            }
            """

    client = RetryFakeLLMClient()
    extractor = LLMExtractor(client, max_attempts=2)

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

    assert result.data["total"] == 15000
    assert client.call_count == 2

    retry_prompt = client.prompts[1]

    assert "previous response" in retry_prompt.lower()
    assert "valid number" in retry_prompt.lower()


def test_llm_extractor_preserves_schema_in_retry_prompt():
    class RetryFakeLLMClient:
        model = "test-model"
        def __init__(self):
            self.call_count = 0
            self.prompts = []

        def generate(self, prompt: str) -> str:
            self.call_count += 1
            self.prompts.append(prompt)

            if self.call_count == 1:
                return """
                {
                    "invoice_number": "INV-123",
                    "vendor_name": "ABC Pvt Ltd",
                    "total": "invalid"
                }
                """

            return """
            {
                "invoice_number": "INV-123",
                "vendor_name": "ABC Pvt Ltd",
                "total": 15000
            }
            """

    client = RetryFakeLLMClient()
    extractor = LLMExtractor(client, max_attempts=2)

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

    assert result.data["total"] == 15000
    assert client.call_count == 2

    retry_prompt = client.prompts[1]

    assert "Expected response schema:" in retry_prompt
    assert "invoice_number" in retry_prompt
    assert "vendor_name" in retry_prompt
    assert "total" in retry_prompt


def test_llm_extractor_rejects_invalid_max_attempts():
    client = FakeLLMClient()

    with pytest.raises(
        ValueError,
        match="max_attempts must be at least 1",
    ):
        LLMExtractor(client, max_attempts=0)


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

def test_llm_extractor_reports_attempt_count():
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

    assert result.metadata["attempts"] == 1


def test_llm_extractor_reports_retry_attempt_count():
    class RetryFakeLLMClient:
        model = "test-model"

        def __init__(self):
            self.call_count = 0

        def generate(self, prompt: str) -> str:
            self.call_count += 1

            if self.call_count == 1:
                return "This is not valid JSON."

            return """
            {
                "invoice_number": "INV-123",
                "vendor_name": "ABC Pvt Ltd",
                "total": 15000
            }
            """

    client = RetryFakeLLMClient()
    extractor = LLMExtractor(client, max_attempts=2)

    content = DocumentContent(
        filename="invoice.pdf",
        document_type="pdf",
        text="Invoice INV-123 ABC Pvt Ltd Total 15000",
    )

    request = ExtractionRequest(
        query="Extract invoice details",
    )

    result = extractor.extract(content, request)

    assert result.metadata["attempts"] == 2


def test_llm_extractor_reports_multiple_retry_attempts():
    class RetryFakeLLMClient:
        model = "test-model"

        def __init__(self):
            self.call_count = 0

        def generate(self, prompt: str) -> str:
            self.call_count += 1

            if self.call_count < 3:
                return "This is not valid JSON."

            return """
            {
                "invoice_number": "INV-123",
                "vendor_name": "ABC Pvt Ltd",
                "total": 15000
            }
            """

    client = RetryFakeLLMClient()
    extractor = LLMExtractor(client, max_attempts=3)

    content = DocumentContent(
        filename="invoice.pdf",
        document_type="pdf",
        text="Invoice INV-123 ABC Pvt Ltd Total 15000",
    )

    request = ExtractionRequest(
        query="Extract invoice details",
    )

    result = extractor.extract(content, request)

    assert result.metadata["attempts"] == 3


def test_llm_extractor_metadata_does_not_change_extracted_data():
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

    assert result.metadata["attempts"] == 1
    assert result.metadata["duration_ms"] >= 0


def test_llm_extractor_reports_metadata_without_schema():
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

    assert result.metadata["attempts"] == 1


def test_llm_extractor_reports_duration():
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

    assert "duration_ms" in result.metadata
    assert result.metadata["duration_ms"] >= 0


def test_llm_extractor_reports_duration_after_retry():
    class RetryFakeLLMClient:
        model = "test-model"

        def __init__(self):
            self.call_count = 0

        def generate(self, prompt: str) -> str:
            self.call_count += 1

            if self.call_count == 1:
                return "This is not valid JSON."

            return """
            {
                "invoice_number": "INV-123",
                "vendor_name": "ABC Pvt Ltd",
                "total": 15000
            }
            """

    client = RetryFakeLLMClient()
    extractor = LLMExtractor(client, max_attempts=2)

    content = DocumentContent(
        filename="invoice.pdf",
        document_type="pdf",
        text="Invoice INV-123 ABC Pvt Ltd Total 15000",
    )

    request = ExtractionRequest(
        query="Extract invoice details",
    )

    result = extractor.extract(content, request)

    assert result.metadata["attempts"] == 2
    assert result.metadata["duration_ms"] >= 0


def test_llm_extractor_reports_complete_metadata():
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

    assert result.data["invoice_number"] == "INV-123"
    assert result.data["vendor_name"] == "ABC Pvt Ltd"
    assert result.data["total"] == 15000

    assert result.metadata["attempts"] == 1
    assert result.metadata["duration_ms"] >= 0


def test_llm_extractor_reports_duration_without_schema():
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

    assert result.metadata["attempts"] == 1
    assert result.metadata["duration_ms"] >= 0


def test_llm_extractor_reports_model_metadata():
    class ModelFakeLLMClient:
        model = "test-model"

        def generate(self, prompt: str) -> str:
            return """
            {
                "invoice_number": "INV-123",
                "vendor_name": "ABC Pvt Ltd",
                "total": 15000
            }
            """

    client = ModelFakeLLMClient()
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

    assert result.metadata["model"] == "test-model"


def test_llm_extractor_reports_model_metadata_after_retry():
    class RetryModelFakeLLMClient:
        model = "test-model"

        def __init__(self):
            self.call_count = 0

        def generate(self, prompt: str) -> str:
            self.call_count += 1

            if self.call_count == 1:
                return "This is not valid JSON."

            return """
            {
                "invoice_number": "INV-123",
                "vendor_name": "ABC Pvt Ltd",
                "total": 15000
            }
            """

    client = RetryModelFakeLLMClient()
    extractor = LLMExtractor(client, max_attempts=2)

    content = DocumentContent(
        filename="invoice.pdf",
        document_type="pdf",
        text="Invoice INV-123 ABC Pvt Ltd Total 15000",
    )

    request = ExtractionRequest(
        query="Extract invoice details",
    )

    result = extractor.extract(content, request)

    assert result.metadata["attempts"] == 2
    assert result.metadata["model"] == "test-model"


def test_llm_extractor_reports_model_metadata_without_schema():
    class ModelFakeLLMClient:
        model = "test-model"

        def generate(self, prompt: str) -> str:
            return """
            {
                "invoice_number": "INV-123",
                "vendor_name": "ABC Pvt Ltd",
                "total": 15000
            }
            """

    client = ModelFakeLLMClient()
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

    assert result.metadata["attempts"] == 1
    assert result.metadata["model"] == "test-model"


def test_llm_extractor_parses_field_metadata():
    class MetadataFakeLLMClient:
        model = "test-model"

        def generate(self, prompt: str) -> str:
            return """
            {
                "data": {
                    "invoice_number": "INV-123",
                    "vendor_name": "ABC Pvt Ltd",
                    "total": 15000
                },
                "field_metadata": {
                    "invoice_number": {
                        "confidence": 0.98,
                        "source_pages": [1]
                    },
                    "vendor_name": {
                        "confidence": 0.95,
                        "source_pages": [1]
                    },
                    "total": {
                        "confidence": 0.62,
                        "source_pages": [2]
                    }
                }
            }
            """

    from document_reader.domain.content import DocumentContent

    content = DocumentContent(
        filename="invoice.pdf",
        document_type="pdf",
        text="Invoice INV-123 ABC Pvt Ltd Total 15000",
        pages=("Invoice INV-123 ABC Pvt Ltd", "Total 15000"),
    )

    result = LLMExtractor(MetadataFakeLLMClient()).extract(
        content,
        ExtractionRequest(query="Extract invoice details"),
    )

    assert result.data["invoice_number"] == "INV-123"
    assert result.field_metadata["invoice_number"].confidence == 0.98
    assert result.field_metadata["invoice_number"].source_pages == (1,)
    assert result.field_metadata["total"].source_pages == (2,)
    assert result.field_metadata["total"].is_low_confidence(threshold=0.7)


def test_llm_extractor_supports_legacy_plain_json_response():
    result = LLMExtractor(FakeLLMClient()).extract(
        DocumentContent(
            filename="invoice.txt",
            document_type="txt",
            text="Invoice INV-123 ABC Pvt Ltd Total 15000",
        ),
        ExtractionRequest(query="Extract invoice details"),
    )

    assert result.data["invoice_number"] == "INV-123"
    assert result.field_metadata == {}


@pytest.mark.parametrize(
    "field_metadata",
    [
        {"total": {"confidence": 1.5, "source_pages": [1]}},
        {"total": {"confidence": 0.8, "source_pages": [0]}},
        {"total": {"confidence": 0.8, "source_pages": "1"}},
        [],
    ],
)
def test_llm_extractor_rejects_invalid_field_metadata(field_metadata):
    import json

    class InvalidMetadataClient:
        model = "test-model"

        def generate(self, prompt: str) -> str:
            return json.dumps(
                {
                    "data": {"total": 100},
                    "field_metadata": field_metadata,
                }
            )

    content = DocumentContent(
        filename="invoice.txt",
        document_type="txt",
        text="Total 100",
    )

    with pytest.raises(ExtractionParsingError, match="metadata"):
        LLMExtractor(InvalidMetadataClient()).extract(
            content,
            ExtractionRequest(query="Extract total"),
        )


def test_llm_extractor_prompt_requests_confidence_and_page_evidence():
    client = FakeLLMClient()
    extractor = LLMExtractor(client)

    content = DocumentContent(
        filename="invoice.pdf",
        document_type="pdf",
        text="Invoice INV-123 Total 15000",
        pages=("Invoice INV-123", "Total 15000"),
    )

    extractor.extract(
        content,
        ExtractionRequest(query="Extract invoice details"),
    )

    prompt = client.last_prompt

    assert "confidence" in prompt
    assert "source_pages" in prompt
    assert "Page 1" in prompt
    assert "Page 2" in prompt


def test_llm_extractor_rejects_metadata_for_unknown_fields():
    class UnknownMetadataFieldClient:
        model = "test-model"

        def generate(self, prompt: str) -> str:
            return """
            {
                "data": {"total": 100},
                "field_metadata": {
                    "missing_field": {
                        "confidence": 0.9,
                        "source_pages": [1]
                    }
                }
            }
            """

    content = DocumentContent(
        filename="invoice.txt",
        document_type="txt",
        text="Total 100",
    )

    with pytest.raises(ExtractionParsingError, match="unknown field"):
        LLMExtractor(UnknownMetadataFieldClient()).extract(
            content,
            ExtractionRequest(query="Extract total"),
        )
