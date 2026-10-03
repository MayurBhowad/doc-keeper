from typing import Any

from document_reader.domain.validation import ExtractionValidationError


class ExtractionValidator:

    SUPPORTED_TYPES = {"string", "number", "boolean"}

    def validate(
        self,
        data: dict[str, Any],
        schema: dict[str, str],
    ) -> None:
        for field, expected_type in schema.items():
            if expected_type not in self.SUPPORTED_TYPES:
                raise ExtractionValidationError(
                    f"Unsupported schema type '{expected_type}' "
                    f"for field '{field}'."
                )

            if field not in data:
                raise ExtractionValidationError(
                    f"Missing required field '{field}'."
                )

            value = data[field]

            if not self._matches_type(value, expected_type):
                actual_type = self._type_name(value)

                raise ExtractionValidationError(
                    f"Field '{field}' expected {expected_type} "
                    f"but received {actual_type}."
                )

    def _matches_type(self, value: Any, expected_type: str) -> bool:
        if expected_type == "string":
            return isinstance(value, str)

        if expected_type == "number":
            return isinstance(value, (int, float)) and not isinstance(value, bool)

        if expected_type == "boolean":
            return isinstance(value, bool)

        return False

    def _type_name(self, value: Any) -> str:
        if isinstance(value, bool):
            return "boolean"

        if isinstance(value, (int, float)):
            return "number"

        if isinstance(value, str):
            return "string"

        return type(value).__name__