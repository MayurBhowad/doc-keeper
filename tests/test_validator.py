import pytest

from document_reader.domain.schema import ExtractionSchema
from document_reader.domain.validation import ExtractionValidationError
from document_reader.domain.validator import ExtractionValidator


class InvoiceExtraction(ExtractionSchema):
    invoice_number: str
    vendor_name: str
    total: float


class SimpleExtraction(ExtractionSchema):
    total: float


def test_validator_accepts_valid_data():
    validator = ExtractionValidator()

    result = validator.validate(
        {
            "invoice_number": "INV-123",
            "vendor_name": "ABC Pvt Ltd",
            "total": 15000,
        },
        InvoiceExtraction,
    )

    assert result == {
        "invoice_number": "INV-123",
        "vendor_name": "ABC Pvt Ltd",
        "total": 15000,
    }


def test_validator_rejects_missing_field():
    validator = ExtractionValidator()

    with pytest.raises(
        ExtractionValidationError,
        match="Field required",
    ):
        validator.validate(
            {
                "invoice_number": "INV-123",
                "vendor_name": "ABC Pvt Ltd",
            },
            InvoiceExtraction,
        )


def test_validator_rejects_wrong_type():
    validator = ExtractionValidator()

    with pytest.raises(
        ExtractionValidationError,
        match="valid number",
    ):
        validator.validate(
            {
                "invoice_number": "INV-123",
                "vendor_name": "ABC Pvt Ltd",
                "total": "15000",
            },
            InvoiceExtraction,
        )


def test_validator_rejects_boolean_as_number():
    validator = ExtractionValidator()

    with pytest.raises(
        ExtractionValidationError,
        match="valid number",
    ):
        validator.validate(
            {"total": True},
            SimpleExtraction,
        )


def test_validator_rejects_unexpected_field():
    validator = ExtractionValidator()

    with pytest.raises(
        ExtractionValidationError,
        match="Extra inputs are not permitted",
    ):
        validator.validate(
            {
                "invoice_number": "INV-123",
                "vendor_name": "ABC Pvt Ltd",
                "total": 15000,
                "unexpected": "value",
            },
            InvoiceExtraction,
        )
