import pytest

from document_reader.domain.extraction import ExtractionResult
from document_reader.domain.review import ReviewRecord, ReviewStatus


def test_review_record_starts_pending():
    record = ReviewRecord(
        extraction=ExtractionResult(data={"total": 100})
    )

    assert record.status is ReviewStatus.PENDING
    assert record.corrected_data == {}
    assert record.effective_data == {"total": 100}


def test_review_record_preserves_original_and_applies_correction():
    record = ReviewRecord(
        extraction=ExtractionResult(data={"total": 100})
    )

    record.correct_field("total", 120)

    assert record.extraction.data == {"total": 100}
    assert record.corrected_data == {"total": 120}
    assert record.effective_data == {"total": 120}
    assert record.status is ReviewStatus.PENDING


def test_review_record_can_be_approved():
    record = ReviewRecord(
        extraction=ExtractionResult(data={"total": 100})
    )

    record.approve()

    assert record.status is ReviewStatus.APPROVED


def test_review_record_can_be_rejected():
    record = ReviewRecord(
        extraction=ExtractionResult(data={"total": 100})
    )

    record.reject()

    assert record.status is ReviewStatus.REJECTED


@pytest.mark.parametrize("action", ["correct_field", "approve", "reject"])
def test_terminal_review_cannot_be_changed(action):
    record = ReviewRecord(
        extraction=ExtractionResult(data={"total": 100})
    )
    record.approve()

    if action == "correct_field":
        with pytest.raises(ValueError):
            record.correct_field("total", 120)
    else:
        with pytest.raises(ValueError):
            getattr(record, action)()


def test_review_record_rejects_unknown_field_correction():
    record = ReviewRecord(
        extraction=ExtractionResult(data={"total": 100})
    )

    with pytest.raises(ValueError, match="Unknown field"):
        record.correct_field("missing_field", 120)
