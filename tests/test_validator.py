import pytest

from document_reader.domain.validation import ExtractionValidationError
from document_reader.domain.validator import ExtractionValidator


def test_validator_accepts_valid_data():
    validator = ExtractionValidator()

    validator.validate(
        {
            "invoice_number": "INV-123",
            "vendor_name": "ABC Pvt Ltd",
            "total": 15000,
            "paid": True,
        },
        {
            "invoice_number": "string",
            "vendor_name": "string",
            "total": "number",
            "paid": "boolean",
        },
    )


def test_validator_rejects_missing_field():
    validator = ExtractionValidator()

    with pytest.raises(
        ExtractionValidationError,
        match="Missing required field 'total'",
    ):
        validator.validate(
            {
                "invoice_number": "INV-123",
                "vendor_name": "ABC Pvt Ltd",
            },
            {
                "invoice_number": "string",
                "vendor_name": "string",
                "total": "number",
            },
        )


def test_validator_rejects_wrong_type():
    validator = ExtractionValidator()

    with pytest.raises(
        ExtractionValidationError,
        match="Field 'total' expected number but received string",
    ):
        validator.validate(
            {
                "invoice_number": "INV-123",
                "vendor_name": "ABC Pvt Ltd",
                "total": "15000",
            },
            {
                "invoice_number": "string",
                "vendor_name": "string",
                "total": "number",
            },
        )


def test_validator_rejects_boolean_as_number():
    validator = ExtractionValidator()

    with pytest.raises(
        ExtractionValidationError,
        match="Field 'total' expected number but received boolean",
    ):
        validator.validate(
            {"total": True},
            {"total": "number"},
        )


def test_validator_rejects_unsupported_type():
    validator = ExtractionValidator()

    with pytest.raises(
        ExtractionValidationError,
        match="Unsupported schema type 'date'",
    ):
        validator.validate(
            {"invoice_date": "2026-10-03"},
            {"invoice_date": "date"},
        )