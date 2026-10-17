from dataclasses import dataclass
from math import isfinite
from typing import Any, Literal

from pydantic import ValidationError

from document_reader.domain.schema import ExtractionSchema
from document_reader.domain.validation import ExtractionValidationError


class ExtractionValidator:
    def validate(
        self,
        data: dict[str, Any],
        schema: type[ExtractionSchema],
    ) -> dict[str, Any]:
        try:
            result = schema.model_validate(data)
        except ValidationError as exc:
            issues = [
                {
                    "field": ".".join(str(part) for part in error["loc"]),
                    "type": error["type"],
                    "message": error["msg"],
                }
                for error in exc.errors()
            ]

            raise ExtractionValidationError(
                str(exc),
                issues=issues,
            ) from exc

        return result.model_dump()


@dataclass(frozen=True)
class BusinessRule:
    field: str
    rule: Literal["positive"]

    def __post_init__(self) -> None:
        if not isinstance(self.field, str) or not self.field.strip():
            raise ValueError("Business rule field must be a non-empty string")

        if self.rule != "positive":
            raise ValueError(f"Unsupported business rule: {self.rule}")


class BusinessValidator:
    def __init__(self, rules: list[BusinessRule] | None = None):
        self.rules = tuple(rules or [])

    def validate(
        self,
        data: dict[str, Any],
        raise_on_error: bool = False,
    ) -> list[dict[str, str]]:
        issues: list[dict[str, str]] = []

        for rule in self.rules:
            value = data.get(rule.field)

            valid_number = (
                isinstance(value, (int, float))
                and not isinstance(value, bool)
                and isfinite(value)
            )

            if not valid_number or value <= 0:
                issues.append(
                    {
                        "field": rule.field,
                        "type": rule.rule,
                        "message": (
                            f"Field '{rule.field}' must be a positive, finite number."
                        ),
                    }
                )

        if issues and raise_on_error:
            raise ExtractionValidationError(
                "Business-rule validation failed.",
                issues=issues,
            )

        return issues
