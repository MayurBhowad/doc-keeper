from document_reader.domain.extraction import ExtractionResult
from document_reader.domain.review import ReviewStatus
from document_reader.services.review import ReviewService
from document_reader.storage.review_json import ReviewJsonStorage


def test_service_creates_and_loads_review(tmp_path):
    service = ReviewService(ReviewJsonStorage(tmp_path / "reviews"))

    record = service.create(
        "invoice-1",
        ExtractionResult(data={"total": 100}),
    )

    assert record.status is ReviewStatus.PENDING
    assert service.get("invoice-1").effective_data == {"total": 100}


def test_service_corrects_and_approves_review(tmp_path):
    service = ReviewService(ReviewJsonStorage(tmp_path / "reviews"))
    service.create("invoice-2", ExtractionResult(data={"total": 100}))

    record = service.correct("invoice-2", "total", 120)
    assert record.effective_data == {"total": 120}

    record = service.approve("invoice-2")
    assert record.status is ReviewStatus.APPROVED

    loaded = service.get("invoice-2")
    assert loaded.extraction.data == {"total": 100}
    assert loaded.effective_data == {"total": 120}
    assert loaded.status is ReviewStatus.APPROVED


def test_service_rejects_review_and_persists_status(tmp_path):
    service = ReviewService(ReviewJsonStorage(tmp_path / "reviews"))
    service.create("invoice-3", ExtractionResult(data={"total": 100}))

    record = service.reject("invoice-3")

    assert record.status is ReviewStatus.REJECTED
    assert service.get("invoice-3").status is ReviewStatus.REJECTED


def test_service_does_not_overwrite_existing_review(tmp_path):
    service = ReviewService(ReviewJsonStorage(tmp_path / "reviews"))
    service.create("invoice-duplicate", ExtractionResult(data={"total": 100}))
    service.correct("invoice-duplicate", "total", 120)
    service.approve("invoice-duplicate")

    import pytest

    with pytest.raises(FileExistsError):
        service.create(
            "invoice-duplicate",
            ExtractionResult(data={"total": 999}),
        )

    loaded = service.get("invoice-duplicate")
    assert loaded.extraction.data == {"total": 100}
    assert loaded.effective_data == {"total": 120}
    assert loaded.status is ReviewStatus.APPROVED


def test_service_cannot_correct_approved_review(tmp_path):
    import pytest

    service = ReviewService(ReviewJsonStorage(tmp_path / "reviews"))
    service.create("invoice-approved", ExtractionResult(data={"total": 100}))
    service.approve("invoice-approved")

    with pytest.raises(ValueError, match="Cannot modify"):
        service.correct("invoice-approved", "total", 200)

    loaded = service.get("invoice-approved")
    assert loaded.status is ReviewStatus.APPROVED
    assert loaded.effective_data == {"total": 100}


def test_service_cannot_approve_rejected_review(tmp_path):
    import pytest

    service = ReviewService(ReviewJsonStorage(tmp_path / "reviews"))
    service.create("invoice-rejected", ExtractionResult(data={"total": 100}))
    service.reject("invoice-rejected")

    with pytest.raises(ValueError, match="Cannot modify"):
        service.approve("invoice-rejected")

    assert service.get("invoice-rejected").status is ReviewStatus.REJECTED
