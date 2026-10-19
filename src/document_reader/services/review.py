from document_reader.domain.extraction import ExtractionResult
from document_reader.domain.review import ReviewRecord
from document_reader.storage.review_json import ReviewJsonStorage


class ReviewService:
    """Coordinate human-review operations and persistence."""

    def __init__(self, storage: ReviewJsonStorage):
        self.storage = storage

    def create(
        self,
        review_id: str,
        extraction: ExtractionResult,
    ) -> ReviewRecord:
        record = ReviewRecord(extraction=extraction)
        self.storage.create(review_id, record)
        return record

    def get(self, review_id: str) -> ReviewRecord:
        return self.storage.load(review_id)

    def correct(
        self,
        review_id: str,
        field_name: str,
        value: object,
    ) -> ReviewRecord:
        record = self.get(review_id)
        record.correct_field(field_name, value)
        self.storage.save(review_id, record)
        return record

    def approve(self, review_id: str) -> ReviewRecord:
        record = self.get(review_id)
        record.approve()
        self.storage.save(review_id, record)
        return record

    def reject(self, review_id: str) -> ReviewRecord:
        record = self.get(review_id)
        record.reject()
        self.storage.save(review_id, record)
        return record
