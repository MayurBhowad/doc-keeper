from typing import Any

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
            raise ExtractionValidationError(
                str(exc)
            ) from exc

        return result.model_dump()
