import json
import pytest

from document_reader.domain.extraction import ExtractionResult, FieldMetadata
from document_reader.domain.review import ReviewRecord
from document_reader.storage.review_json import ReviewJsonStorage


def test_review_storage_persists_pending_record(tmp_path):
    storage = ReviewJsonStorage(tmp_path / "reviews")
    record = ReviewRecord(
        extraction=ExtractionResult(
            data={"total": 100},
            field_metadata={
                "total": FieldMetadata(
                    confidence=0.6,
                    source_pages=(1,),
                )
            },
        )
    )

    path = storage.save("invoice-1", record)
    saved = json.loads(path.read_text(encoding="utf-8"))

    assert saved["review_id"] == "invoice-1"
    assert saved["status"] == "pending"
    assert saved["original_data"] == {"total": 100}
    assert saved["corrected_data"] == {}
    assert saved["effective_data"] == {"total": 100}
    assert saved["field_metadata"]["total"] == {
        "confidence": 0.6,
        "source_pages": [1],
    }


def test_review_storage_persists_corrections_and_status(tmp_path):
    storage = ReviewJsonStorage(tmp_path / "reviews")
    record = ReviewRecord(
        extraction=ExtractionResult(data={"total": 100})
    )
    record.correct_field("total", 120)
    record.approve()

    path = storage.save("invoice-2", record)
    saved = json.loads(path.read_text(encoding="utf-8"))

    assert saved["status"] == "approved"
    assert saved["original_data"] == {"total": 100}
    assert saved["corrected_data"] == {"total": 120}
    assert saved["effective_data"] == {"total": 120}


def test_review_storage_does_not_overwrite_another_review(tmp_path):
    storage = ReviewJsonStorage(tmp_path / "reviews")
    first = ReviewRecord(
        extraction=ExtractionResult(data={"total": 100})
    )
    second = ReviewRecord(
        extraction=ExtractionResult(data={"total": 200})
    )

    first_path = storage.save("invoice-1", first)
    second_path = storage.save("invoice-2", second)

    assert first_path != second_path
    assert json.loads(first_path.read_text())["original_data"] == {"total": 100}
    assert json.loads(second_path.read_text())["original_data"] == {"total": 200}


def test_review_storage_loads_saved_corrections_and_status(tmp_path):
    storage = ReviewJsonStorage(tmp_path / "reviews")
    record = ReviewRecord(
        extraction=ExtractionResult(
            data={"total": 100},
            field_metadata={
                "total": FieldMetadata(
                    confidence=0.6,
                    source_pages=(1,),
                )
            },
        )
    )
    record.correct_field("total", 120)
    record.approve()
    storage.save("invoice-3", record)

    loaded = storage.load("invoice-3")

    assert loaded.status.value == "approved"
    assert loaded.extraction.data == {"total": 100}
    assert loaded.corrected_data == {"total": 120}
    assert loaded.effective_data == {"total": 120}
    assert loaded.extraction.field_metadata["total"].confidence == 0.6
    assert loaded.extraction.field_metadata["total"].source_pages == (1,)


def test_review_storage_raises_for_missing_record(tmp_path):
    storage = ReviewJsonStorage(tmp_path / "reviews")

    with pytest.raises(FileNotFoundError):
        storage.load("missing-review")


def test_review_storage_rejects_malformed_json(tmp_path):
    storage = ReviewJsonStorage(tmp_path / "reviews")
    (tmp_path / "reviews" / "broken.json").write_text(
        "{not valid json",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Invalid review record"):
        storage.load("broken")


@pytest.mark.parametrize("review_id", ["invoice:1", "invoice?1", "invoice 1"])
def test_review_storage_rejects_unsafe_review_ids(tmp_path, review_id):
    storage = ReviewJsonStorage(tmp_path / "reviews")

    with pytest.raises(ValueError, match="filename-safe"):
        storage.save(
            review_id,
            ReviewRecord(extraction=ExtractionResult(data={"total": 100})),
        )


def test_review_storage_preserves_extraction_metadata(tmp_path):
    storage = ReviewJsonStorage(tmp_path / "reviews")
    extraction = ExtractionResult(
        data={"total": 100},
        metadata={"extractor": "test", "version": 1},
    )
    record = ReviewRecord(extraction=extraction)

    storage.save("metadata-review", record)
    loaded = storage.load("metadata-review")

    assert loaded.extraction.metadata == {
        "extractor": "test",
        "version": 1,
    }


def test_review_storage_create_rejects_existing_id(tmp_path):
    storage = ReviewJsonStorage(tmp_path / "reviews")
    original = ReviewRecord(
        extraction=ExtractionResult(data={"total": 100})
    )
    replacement = ReviewRecord(
        extraction=ExtractionResult(data={"total": 999})
    )

    storage.create("invoice-1", original)

    with pytest.raises(FileExistsError):
        storage.create("invoice-1", replacement)

    assert storage.load("invoice-1").extraction.data == {"total": 100}


def test_review_storage_save_updates_existing_record(tmp_path):
    storage = ReviewJsonStorage(tmp_path / "reviews")
    record = ReviewRecord(
        extraction=ExtractionResult(data={"total": 100})
    )
    storage.create("invoice-1", record)

    record.correct_field("total", 120)
    storage.save("invoice-1", record)

    loaded = storage.load("invoice-1")
    assert loaded.extraction.data == {"total": 100}
    assert loaded.effective_data == {"total": 120}


@pytest.mark.parametrize(
    "field_metadata",
    [
        {"total": {"confidence": "high", "source_pages": [1]}},
        {"total": {"confidence": 0.5, "source_pages": [0]}},
        {"total": {"confidence": 0.5, "source_pages": "page one"}},
        {"total": None},
    ],
)
def test_review_storage_rejects_invalid_field_metadata(
    tmp_path, field_metadata
):
    storage = ReviewJsonStorage(tmp_path / "reviews")
    path = tmp_path / "reviews" / "broken.json"
    path.write_text(
        json.dumps({
            "review_id": "broken",
            "status": "pending",
            "original_data": {"total": 100},
            "corrected_data": {},
            "effective_data": {"total": 100},
            "field_metadata": field_metadata,
        }),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        storage.load("broken")


def test_review_storage_rejects_non_json_metadata(tmp_path):
    storage = ReviewJsonStorage(tmp_path / "reviews")
    record = ReviewRecord(
        extraction=ExtractionResult(
            data={"total": 100},
            metadata={"invalid": object()},
        )
    )

    with pytest.raises((TypeError, ValueError)):
        storage.save("invalid-metadata", record)


def test_review_storage_create_does_not_leave_file_for_invalid_metadata(
    tmp_path,
):
    storage = ReviewJsonStorage(tmp_path / "reviews")
    record = ReviewRecord(
        extraction=ExtractionResult(
            data={"total": 100},
            metadata={"invalid": object()},
        )
    )

    with pytest.raises((TypeError, ValueError)):
        storage.create("invalid-metadata", record)

    assert not (tmp_path / "reviews" / "invalid-metadata.json").exists()


@pytest.mark.parametrize("metadata", [["unexpected"], "unexpected", 42])
def test_review_storage_rejects_invalid_extraction_metadata(
    tmp_path, metadata
):
    storage = ReviewJsonStorage(tmp_path / "reviews")
    path = tmp_path / "reviews" / "broken.json"
    path.write_text(
        json.dumps({
            "review_id": "broken",
            "status": "pending",
            "original_data": {"total": 100},
            "metadata": metadata,
            "corrected_data": {},
            "effective_data": {"total": 100},
            "field_metadata": {},
        }),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="metadata must be an object or null"):
        storage.load("broken")
