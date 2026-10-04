import pytest
from pydantic import ValidationError

from document_reader.domain.schema import ExtractionSchema


class InvoiceExtraction(ExtractionSchema):
    invoice_number: str
    vendor_name: str
    total: float


def test_extraction_schema_validates_valid_data():
    result = InvoiceExtraction(
        invoice_number="INV-123",
        vendor_name="ABC Pvt Ltd",
        total=15000,
    )

    assert result.invoice_number == "INV-123"
    assert result.vendor_name == "ABC Pvt Ltd"
    assert result.total == 15000


def test_extraction_schema_generates_json_schema():
    schema = InvoiceExtraction.model_json_schema()

    assert schema["type"] == "object"
    assert schema["properties"]["invoice_number"]["type"] == "string"
    assert schema["properties"]["vendor_name"]["type"] == "string"
    assert schema["properties"]["total"]["type"] == "number"

    assert set(schema["required"]) == {
        "invoice_number",
        "vendor_name",
        "total",
    }


def test_extraction_schema_rejects_unexpected_fields():
    data = {
        "invoice_number": "INV-123",
        "vendor_name": "ABC Pvt Ltd",
        "total": 15000,
        "unexpected": "value",
    }

    with pytest.raises(ValidationError):
        InvoiceExtraction.model_validate(data)