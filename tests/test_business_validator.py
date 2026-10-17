import pytest

from document_reader.domain.validation import ExtractionValidationError
from document_reader.domain.validator import BusinessRule, BusinessValidator


def test_positive_number_rule_accepts_positive_value():
    validator = BusinessValidator(
        rules=[BusinessRule(field="total", rule="positive")]
    )

    assert validator.validate({"total": 15000}) == []


def test_positive_number_rule_reports_negative_value():
    validator = BusinessValidator(
        rules=[BusinessRule(field="total", rule="positive")]
    )

    issues = validator.validate({"total": -10})

    assert len(issues) == 1
    assert issues[0]["field"] == "total"
    assert issues[0]["type"] == "positive"
    assert "positive" in issues[0]["message"].lower()


def test_positive_number_rule_rejects_boolean():
    validator = BusinessValidator(
        rules=[BusinessRule(field="total", rule="positive")]
    )

    issues = validator.validate({"total": True})

    assert len(issues) == 1
    assert issues[0]["field"] == "total"


def test_business_validator_can_raise_structured_error():
    validator = BusinessValidator(
        rules=[BusinessRule(field="total", rule="positive")]
    )

    with pytest.raises(ExtractionValidationError) as error:
        validator.validate(
            {"total": -10},
            raise_on_error=True,
        )

    assert error.value.issues[0]["field"] == "total"


def test_business_rule_rejects_unknown_rule():
    with pytest.raises(ValueError, match="Unsupported business rule"):
        BusinessRule(field="total", rule="unknown")
