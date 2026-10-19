import json
import re
from pathlib import Path
from typing import Any

from document_reader.domain.extraction import ExtractionResult, FieldMetadata
from document_reader.domain.review import ReviewRecord, ReviewStatus


class ReviewJsonStorage:
    """Persist and restore human-review records."""

    def __init__(self, output_dir: str | Path = "output/reviews"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, review_id: str) -> Path:
        if not isinstance(review_id, str) or not review_id.strip():
            raise ValueError("review_id must be a non-empty string")

        if not re.fullmatch(r"[A-Za-z0-9_.-]+", review_id) or review_id in {".", ".."}:
            raise ValueError("review_id must be a filename-safe identifier")

        return self.output_dir / f"{review_id}.json"

    def _serialize(self, review_id: str, record: ReviewRecord) -> dict:
        return {
            "review_id": review_id,
            "status": record.status.value,
            "original_data": record.extraction.data,
            "metadata": record.extraction.metadata,
            "corrected_data": record.corrected_data,
            "effective_data": record.effective_data,
            "field_metadata": {
                name: {
                    "confidence": metadata.confidence,
                    "source_pages": list(metadata.source_pages),
                }
                for name, metadata in record.extraction.field_metadata.items()
            },
        }

    def save(self, review_id: str, record: ReviewRecord) -> Path:
        if not isinstance(record, ReviewRecord):
            raise TypeError("record must be a ReviewRecord")

        output_path = self._path_for(review_id)
        data = self._serialize(review_id, record)

        output_path.write_text(
            json.dumps(data, indent=2, allow_nan=False),
            encoding="utf-8",
        )
        return output_path

    def create(self, review_id: str, record: ReviewRecord) -> Path:
        """Create a review without overwriting an existing record."""
        if not isinstance(record, ReviewRecord):
            raise TypeError("record must be a ReviewRecord")

        output_path = self._path_for(review_id)
        data = self._serialize(review_id, record)
        payload = json.dumps(data, indent=2, allow_nan=False) + "\n"

        try:
            with output_path.open("x", encoding="utf-8") as file:
                file.write(payload)
        except FileExistsError:
            raise FileExistsError(
                f"Review already exists: {review_id}"
            ) from None

        return output_path

    def load(self, review_id: str) -> ReviewRecord:
        path = self._path_for(review_id)
        if not path.exists():
            raise FileNotFoundError(f"Review record not found: {review_id}")

        try:
            saved: Any = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(saved, dict):
                raise ValueError("Review record must be a JSON object")

            if saved.get("review_id") != review_id:
                raise ValueError("Review ID does not match the requested ID")

            original_data = saved.get("original_data")
            corrected_data = saved.get("corrected_data")
            metadata = saved.get("metadata")
            raw_metadata = saved.get("field_metadata", {})

            if metadata is not None and not isinstance(metadata, dict):
                raise ValueError("metadata must be an object or null")
            if not isinstance(original_data, dict):
                raise ValueError("original_data must be an object")
            if not isinstance(corrected_data, dict):
                raise ValueError("corrected_data must be an object")
            if not isinstance(raw_metadata, dict):
                raise ValueError("field_metadata must be an object")

            field_metadata = {}
            for name, values in raw_metadata.items():
                if not isinstance(name, str) or not isinstance(values, dict):
                    raise ValueError("Invalid field metadata entry")

                pages = values.get("source_pages", [])
                if not isinstance(pages, list):
                    raise ValueError(f"source_pages for '{name}' must be a list")

                field_metadata[name] = FieldMetadata(
                    confidence=values.get("confidence"),
                    source_pages=tuple(pages),
                )

            extraction = ExtractionResult(
                data=original_data,
                metadata=metadata,
                field_metadata=field_metadata,
            )
            record = ReviewRecord(
                extraction=extraction,
                status=ReviewStatus(saved.get("status")),
                corrected_data=corrected_data,
            )

            if saved.get("effective_data") != record.effective_data:
                raise ValueError("effective_data does not match review values")

            return record
        except (json.JSONDecodeError, TypeError, KeyError) as exc:
            raise ValueError(f"Invalid review record '{review_id}'") from exc
