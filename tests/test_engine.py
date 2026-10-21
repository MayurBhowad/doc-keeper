import fitz
from document_reader import storage
from document_reader.engine import DocumentEngine
from document_reader.domain.extraction import ExtractionResult
from document_reader.extractors.llm import LLMExtractor
from document_reader.storage.json import JsonStorage
from document_reader.extractors.fake import FakeExtractor
import json

import pytest

from document_reader.domain.schema import ExtractionSchema
from document_reader.domain.validation import ExtractionValidationError


class FakeLLMClient:
    model = "test-model"

    def generate(self, prompt: str) -> str:
        return """
            {
                "invoice_number": "INV-123",
                "vendor_name": "ABC Pvt Ltd",
                "total": 15000
            }
            """


def test_engine_processes_text_document(tmp_path):
    input_file = tmp_path / "hello.txt"
    input_file.write_text("Hello Document AI!", encoding="utf-8")

    output_dir = tmp_path / "output"

    from document_reader.engine import DocumentEngine

    engine = DocumentEngine(storage=JsonStorage(output_dir))

    result = engine.process(str(input_file), "Extract the document text")

    assert result["filename"] == "hello.txt"
    assert result["data"]["query"] == "Extract the document text"
    assert result["data"]["filename"] == "hello.txt"
    assert result["data"]["text"] == "Hello Document AI!"

    output_file = output_dir / "hello.json"

    assert output_file.exists()


def test_engine_processes_pdf_document(tmp_path):
    input_file = tmp_path / "hello.pdf"

    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "Hello PDF!")
    pdf.save(input_file)
    pdf.close()

    output_dir = tmp_path / "output"

    engine = DocumentEngine(storage=JsonStorage(output_dir))

    result = engine.process(str(input_file), "Extract the document text")

    assert result["filename"] == "hello.pdf"
    assert result["data"]["filename"] == "hello.pdf"
    assert "Hello PDF!" in result["data"]["text"]

    output_file = output_dir / "hello.json"

    assert output_file.exists()


def test_engine_rejects_unsupported_document(tmp_path):
    input_file = tmp_path / "hello.docx"
    input_file.write_text("Hello Document AI!", encoding="utf-8")

    engine = DocumentEngine(extractor=FakeExtractor())

    try:
        engine.process(str(input_file), "Extract the document text")
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Unsupported document type" in str(exc)


def test_engine_with_llm_extractor(tmp_path):
    input_file = tmp_path / "invoice.txt"

    input_file.write_text(
        "Invoice INV-123 ABC Pvt Ltd Total 15000",
        encoding="utf-8",
    )

    output_dir = tmp_path / "output"

    extractor = LLMExtractor(
        FakeLLMClient()
    )

    engine = DocumentEngine(
        extractor=extractor,
        storage=JsonStorage(output_dir),
    )

    result = engine.process(
        str(input_file),
        "Give me invoice number, vendor and total",
    )

    assert result["filename"] == "invoice.txt"
    assert result["data"]["invoice_number"] == "INV-123"
    assert result["data"]["vendor_name"] == "ABC Pvt Ltd"
    assert result["data"]["total"] == 15000

    assert (output_dir / "invoice.json").exists()


def test_engine_passes_schema_to_extractor(tmp_path):
    from pydantic import Field

    from document_reader.domain.schema import ExtractionSchema

    class InvoiceSchema(ExtractionSchema):
        invoice_number: str
        total: int = Field(gt=0)

    class SchemaCapturingExtractor:
        def __init__(self):
            self.request = None

        def extract(self, content, request):
            self.request = request
            return ExtractionResult(
                data={"invoice_number": "INV-123", "total": 15000}
            )

    input_file = tmp_path / "invoice.txt"
    input_file.write_text("Invoice INV-123 Total 15000", encoding="utf-8")

    extractor = SchemaCapturingExtractor()
    engine = DocumentEngine(
        extractor=extractor,
        storage=JsonStorage(tmp_path / "output"),
    )

    engine.process(
        str(input_file),
        "Extract invoice details",
        schema=InvoiceSchema,
    )

    assert extractor.request.schema is InvoiceSchema


def test_engine_extracts_and_validates_invoice_schema(tmp_path):
    from pydantic import Field

    class InvoiceSchema(ExtractionSchema):
        invoice_number: str
        vendor_name: str
        total: int = Field(gt=0)

    class SchemaAwareLLMClient:
        model = "test-model"

        def generate(self, prompt: str) -> str:
            assert "Expected response schema:" in prompt
            return json.dumps({
                "invoice_number": "INV-123",
                "vendor_name": "ABC Pvt Ltd",
                "total": 15000,
            })

    input_file = tmp_path / "invoice.txt"
    input_file.write_text(
        "Invoice INV-123 from ABC Pvt Ltd. Total 15000.",
        encoding="utf-8",
    )

    output_dir = tmp_path / "output"
    engine = DocumentEngine(
        extractor=LLMExtractor(SchemaAwareLLMClient()),
        storage=JsonStorage(output_dir),
    )

    result = engine.process(
        str(input_file),
        "Extract invoice number, vendor, and total",
        schema=InvoiceSchema,
    )

    assert result["data"] == {
        "invoice_number": "INV-123",
        "vendor_name": "ABC Pvt Ltd",
        "total": 15000,
    }

    saved_data = json.loads(
        (output_dir / "invoice.json").read_text(encoding="utf-8")
    )
    assert saved_data["data"] == result["data"]

def test_engine_rejects_invalid_invoice_schema(tmp_path):
    from pydantic import Field

    class InvoiceSchema(ExtractionSchema):
        invoice_number: str
        total: int = Field(gt=0)

    class InvalidLLMClient:
        model = "test-model"

        def generate(self, prompt: str) -> str:
            return '{"invoice_number": "INV-123", "total": -10}'

    input_file = tmp_path / "invoice.txt"
    input_file.write_text("Invoice INV-123 Total -10", encoding="utf-8")

    engine = DocumentEngine(
        extractor=LLMExtractor(InvalidLLMClient(), max_attempts=1),
        storage=JsonStorage(tmp_path / "output"),
    )

    with pytest.raises(ExtractionValidationError):
        engine.process(
            str(input_file),
            "Extract invoice details",
            schema=InvoiceSchema,
        )


def test_engine_rejects_negative_total_with_business_validator(tmp_path):
    from document_reader.domain.validator import BusinessRule, BusinessValidator

    input_file = tmp_path / "invoice.txt"
    input_file.write_text("Invoice total -10", encoding="utf-8")

    class NegativeTotalExtractor:
        def extract(self, content, request):
            return ExtractionResult(data={"total": -10})

    engine = DocumentEngine(
        extractor=NegativeTotalExtractor(),
        storage=JsonStorage(tmp_path / "output"),
        business_validator=BusinessValidator(
            rules=[BusinessRule(field="total", rule="positive")]
        ),
    )

    with pytest.raises(ExtractionValidationError) as error:
        engine.process(str(input_file), "Extract total")

    assert error.value.issues[0]["field"] == "total"
    assert not (tmp_path / "output" / "invoice.json").exists()


def test_engine_saves_result_when_business_rules_pass(tmp_path):
    from document_reader.domain.validator import BusinessRule, BusinessValidator

    input_file = tmp_path / "invoice.txt"
    input_file.write_text("Invoice total 15000", encoding="utf-8")

    class PositiveTotalExtractor:
        def extract(self, content, request):
            return ExtractionResult(data={"total": 15000})

    output_dir = tmp_path / "output"
    engine = DocumentEngine(
        extractor=PositiveTotalExtractor(),
        storage=JsonStorage(output_dir),
        business_validator=BusinessValidator(
            rules=[BusinessRule(field="total", rule="positive")]
        ),
    )

    result = engine.process(str(input_file), "Extract total")

    assert result["data"]["total"] == 15000
    assert (output_dir / "invoice.json").exists()


def test_engine_returns_extraction_metadata(tmp_path):
    from document_reader.domain.extraction import FieldMetadata

    input_file = tmp_path / "invoice.txt"
    input_file.write_text("Invoice INV-123", encoding="utf-8")

    class MetadataExtractor:
        def extract(self, content, request):
            return ExtractionResult(
                data={"invoice_number": "INV-123"},
                metadata={"model": "test-model", "attempts": 1},
                field_metadata={
                    "invoice_number": FieldMetadata(
                        confidence=0.95,
                        source_pages=(1,),
                    )
                },
            )

    engine = DocumentEngine(
        extractor=MetadataExtractor(),
        storage=JsonStorage(tmp_path / "output"),
    )

    result = engine.process(str(input_file), "Extract invoice number")

    assert result["data"] == {"invoice_number": "INV-123"}
    assert result["metadata"] == {"model": "test-model", "attempts": 1}
    assert result["field_metadata"] == {
        "invoice_number": {
            "confidence": 0.95,
            "source_pages": [1],
        }
    }
