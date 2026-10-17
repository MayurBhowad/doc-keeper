import json

from document_reader.domain.extraction import ExtractionResult, FieldMetadata
from document_reader.storage.json import JsonStorage


def test_storage_preserves_existing_json_shape_without_field_metadata(tmp_path):
    storage = JsonStorage(tmp_path / "output")

    path = storage.save(
        "invoice.txt",
        ExtractionResult(data={"total": 15000}),
    )

    saved = json.loads(path.read_text(encoding="utf-8"))

    assert saved == {
        "filename": "invoice.txt",
        "data": {"total": 15000},
    }


def test_storage_persists_field_metadata(tmp_path):
    storage = JsonStorage(tmp_path / "output")

    path = storage.save(
        "invoice.txt",
        ExtractionResult(
            data={"total": 15000},
            field_metadata={
                "total": FieldMetadata(
                    confidence=0.91,
                    source_pages=(2,),
                )
            },
        ),
    )

    saved = json.loads(path.read_text(encoding="utf-8"))

    assert saved["filename"] == "invoice.txt"
    assert saved["data"] == {"total": 15000}
    assert saved["field_metadata"] == {
        "total": {
            "confidence": 0.91,
            "source_pages": [2],
        }
    }
