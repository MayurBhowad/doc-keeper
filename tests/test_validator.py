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


def test_validator_exposes_structured_issues_for_missing_field():
    validator = ExtractionValidator()

    with pytest.raises(ExtractionValidationError) as error:
        validator.validate(
            {
                "invoice_number": "INV-123",
                "vendor_name": "ABC Pvt Ltd",
            },
            InvoiceExtraction,
        )

    assert error.value.issues
    issue = next(
        item for item in error.value.issues
        if item["field"] == "total"
    )
    assert issue["type"] == "missing"
    assert "required" in issue["message"].lower()


def test_validator_exposes_structured_issues_for_extra_field():
    validator = ExtractionValidator()

    with pytest.raises(ExtractionValidationError) as error:
        validator.validate(
            {
                "invoice_number": "INV-123",
                "vendor_name": "ABC Pvt Ltd",
                "total": 15000,
                "unexpected": "value",
            },
            InvoiceExtraction,
        )

    issue = next(
        item for item in error.value.issues
        if item["field"] == "unexpected"
    )
    assert issue["type"] == "extra_forbidden"
    assert issue["message"]


def test_validation_error_string_remains_readable():
    error = ExtractionValidationError(
        "Invalid invoice total",
        issues=[
            {
                "field": "total",
                "type": "greater_than",
                "message": "Value must be positive",
            }
        ],
    )

    assert "Invalid invoice total" in str(error)
    assert error.issues[0]["field"] == "total"
