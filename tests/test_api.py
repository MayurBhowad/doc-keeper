
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from document_reader.engine import DocumentEngine
from document_reader.extractors.fake import FakeExtractor
from document_reader.storage.json import JsonStorage
import document_reader.api as api_module

from document_reader.api import app, get_engine


class FakeEngine:
    def __init__(self, result=None, error=None):
        self.result = result or {
            "filename": "uploaded.txt",
            "data": {"invoice_number": "INV-123"},
            "output": "output/uploaded.json",
            "metadata": {"model": "test-model", "attempts": 1},
            "field_metadata": {
                "invoice_number": {
                    "confidence": 0.95,
                    "source_pages": [1],
                }
            },
        }
        self.error = error
        self.calls = []

    def process(self, path, query, **kwargs):
        self.calls.append((path, query, kwargs))
        if self.error:
            raise self.error
        return self.result


@pytest.fixture
def client():
    engine = FakeEngine()
    app.dependency_overrides[get_engine] = lambda: engine
    with TestClient(app) as test_client:
        yield test_client, engine
    app.dependency_overrides.clear()


def test_extract_returns_503_when_engine_is_not_configured(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    app.dependency_overrides.pop(get_engine, None)

    with TestClient(app, raise_server_exceptions=False) as test_client:
        response = test_client.post(
            "/extract",
            files={
                "file": ("invoice.txt", b"Invoice INV-123", "text/plain")
            },
            data={"query": "Extract invoice number"},
        )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Extraction service is not configured."
    )


def test_create_engine_rejects_missing_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(
        api_module.APIConfigurationError,
        match="Extraction service is not configured.",
    ):
        api_module.create_engine()


def test_health_returns_ok(client):
    test_client, _ = client

    response = test_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_extract_accepts_text_upload(client):
    test_client, engine = client

    response = test_client.post(
        "/extract",
        files={"file": ("invoice.txt", b"Invoice INV-123", "text/plain")},
        data={"query": "Extract invoice number"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "filename": "invoice.txt",
        "data": {"invoice_number": "INV-123"},
        "metadata": {"model": "test-model", "attempts": 1},
        "field_metadata": {
            "invoice_number": {
                "confidence": 0.95,
                "source_pages": [1],
            }
        },
    }
    assert len(engine.calls) == 1
    temp_path, query, _ = engine.calls[0]
    assert query == "Extract invoice number"
    assert not Path(temp_path).exists()


def test_extract_rejects_unsupported_extension(client):
    test_client, engine = client

    response = test_client.post(
        "/extract",
        files={"file": ("invoice.docx", b"not supported", "application/octet-stream")},
        data={"query": "Extract invoice number"},
    )

    assert response.status_code == 415
    assert engine.calls == []


def test_extract_rejects_blank_query(client):
    test_client, engine = client

    response = test_client.post(
        "/extract",
        files={"file": ("invoice.txt", b"Invoice INV-123", "text/plain")},
        data={"query": "   "},
    )

    assert response.status_code == 422
    assert engine.calls == []


def test_extract_returns_generic_error_and_cleans_temp_file():
    engine = FakeEngine(error=RuntimeError("internal details"))
    app.dependency_overrides[get_engine] = lambda: engine

    try:
        with TestClient(app) as test_client:
            response = test_client.post(
                "/extract",
                files={"file": ("invoice.txt", b"Invoice INV-123", "text/plain")},
                data={"query": "Extract invoice number"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 500
    assert response.json()["detail"] == "Document extraction failed."
    temp_path = engine.calls[0][0]
    assert not Path(temp_path).exists()


def test_extract_maps_unexpected_value_error_to_500():
    engine = FakeEngine(error=ValueError("internal implementation detail"))
    app.dependency_overrides[get_engine] = lambda: engine

    try:
        with TestClient(app) as test_client:
            response = test_client.post(
                "/extract",
                files={
                    "file": (
                        "invoice.txt",
                        b"Invoice INV-123",
                        "text/plain",
                    )
                },
                data={"query": "Extract invoice number"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 500
    assert response.json()["detail"] == "Document extraction failed."
    assert "internal implementation detail" not in response.text
    assert not Path(engine.calls[0][0]).exists()


def test_extract_rejects_oversized_upload():
    engine = FakeEngine()
    app.dependency_overrides[get_engine] = lambda: engine

    try:
        with TestClient(app) as test_client:
            response = test_client.post(
                "/extract",
                files={
                    "file": (
                        "large.txt",
                        b"x" * (10 * 1024 * 1024 + 1),
                        "text/plain",
                    )
                },
                data={"query": "Extract text"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 413
    assert engine.calls == []


def test_extract_rejects_request_body_over_limit():
    engine = FakeEngine()
    app.dependency_overrides[get_engine] = lambda: engine

    try:
        with TestClient(app) as test_client:
            response = test_client.post(
                "/extract",
                content=b"x" * (api_module.MAX_REQUEST_BODY_SIZE + 1),
                headers={
                    "Content-Type": "application/octet-stream",
                    "Content-Length": str(
                        api_module.MAX_REQUEST_BODY_SIZE + 1
                    ),
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 413
    assert response.json()["detail"] == (
        "Request body exceeds the permitted size."
    )
    assert engine.calls == []


def test_extract_rejects_missing_file(client):
    test_client, engine = client

    response = test_client.post(
        "/extract",
        data={"query": "Extract invoice number"},
    )

    assert response.status_code == 422
    assert engine.calls == []


def test_extract_rejects_missing_query(client):
    test_client, engine = client

    response = test_client.post(
        "/extract",
        files={"file": ("invoice.txt", b"Invoice INV-123", "text/plain")},
    )

    assert response.status_code == 422
    assert engine.calls == []


def test_extract_rejects_empty_upload(client):
    test_client, engine = client

    response = test_client.post(
        "/extract",
        files={"file": ("invoice.txt", b"", "text/plain")},
        data={"query": "Extract invoice number"},
    )

    assert response.status_code == 422
    assert engine.calls == []


def test_extract_maps_validation_error_and_cleans_temp_file():
    from document_reader.domain.validation import ExtractionValidationError

    engine = FakeEngine(error=ExtractionValidationError("Sensitive internal details"))
    app.dependency_overrides[get_engine] = lambda: engine

    try:
        with TestClient(app) as test_client:
            response = test_client.post(
                "/extract",
                files={"file": ("invoice.txt", b"Invoice INV-123", "text/plain")},
                data={"query": "Extract invoice number"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert "Sensitive internal details" not in response.text
    assert not Path(engine.calls[0][0]).exists()


def test_extract_rejects_malformed_pdf_and_cleans_temp_file(
    tmp_path,
    monkeypatch,
):
    engine = DocumentEngine(
        extractor=FakeExtractor(),
        storage=JsonStorage(tmp_path / "output"),
    )
    app.dependency_overrides[get_engine] = lambda: engine

    try:
        original_named_temp_file = api_module.tempfile.NamedTemporaryFile
        temp_paths = []

        def tracking_temp_file(*args, **kwargs):
            temp_file = original_named_temp_file(*args, **kwargs)
            temp_paths.append(temp_file.name)
            return temp_file

        monkeypatch.setattr(
            api_module.tempfile,
            "NamedTemporaryFile",
            tracking_temp_file,
        )
        with TestClient(app) as test_client:
            response = test_client.post(
                "/extract",
                files={
                    "file": (
                        "broken.pdf",
                        b"not a valid PDF",
                        "application/pdf",
                    )
                },
                data={"query": "Extract invoice number"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "Uploaded document is invalid or unreadable."
    )
    assert "Traceback" not in response.text
    assert len(temp_paths) == 1
    assert not Path(temp_paths[0]).exists()


def test_extract_accepts_valid_pdf_upload(tmp_path):
    import fitz

    pdf_path = tmp_path / "invoice.pdf"
    with fitz.open() as pdf:
        page = pdf.new_page()
        page.insert_text((72, 72), "Invoice INV-123")
        pdf.save(pdf_path)

    pdf_bytes = pdf_path.read_bytes()
    engine = DocumentEngine(
        extractor=FakeExtractor(),
        storage=JsonStorage(tmp_path / "output"),
    )
    app.dependency_overrides[get_engine] = lambda: engine

    try:
        with TestClient(app) as test_client:
            response = test_client.post(
                "/extract",
                files={
                    "file": ("invoice.pdf", pdf_bytes, "application/pdf"),
                },
                data={"query": "Extract invoice number"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "invoice.pdf"
    assert body["data"]["filename"].endswith(".pdf")
    assert "output" not in body



def test_extract_hides_storage_errors_and_cleans_temp_file():
    class StorageFailureEngine(FakeEngine):
        def process(self, path, query, **kwargs):
            self.calls.append((path, query, kwargs))
            raise OSError("Sensitive filesystem path: /srv/private/output.json")

    engine = StorageFailureEngine()
    app.dependency_overrides[get_engine] = lambda: engine

    try:
        with TestClient(app) as test_client:
            response = test_client.post(
                "/extract",
                files={"file": ("invoice.txt", b"Invoice INV-123", "text/plain")},
                data={"query": "Extract invoice number"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 500
    assert response.json()["detail"] == "Document extraction failed."
    assert "/srv/private" not in response.text
    assert not Path(engine.calls[0][0]).exists()


def test_extract_rejects_empty_pdf_and_cleans_temp_file(tmp_path):
    engine = DocumentEngine(
        extractor=FakeExtractor(),
        storage=JsonStorage(tmp_path / "output"),
    )
    app.dependency_overrides[get_engine] = lambda: engine

    try:
        with TestClient(app) as test_client:
            response = test_client.post(
                "/extract",
                files={"file": ("empty.pdf", b"", "application/pdf")},
                data={"query": "Extract invoice number"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["detail"] == "Uploaded file must not be empty."


def test_extract_rejects_invalid_utf8_text_and_cleans_temp_file(
    tmp_path,
    monkeypatch,
):
    engine = DocumentEngine(
        extractor=FakeExtractor(),
        storage=JsonStorage(tmp_path / "output"),
    )
    app.dependency_overrides[get_engine] = lambda: engine
    temp_paths = []

    original_named_temp_file = api_module.tempfile.NamedTemporaryFile

    def tracking_temp_file(*args, **kwargs):
        temp_file = original_named_temp_file(*args, **kwargs)
        temp_paths.append(temp_file.name)
        return temp_file

    monkeypatch.setattr(
        api_module.tempfile,
        "NamedTemporaryFile",
        tracking_temp_file,
    )

    try:
        with TestClient(app) as test_client:
            response = test_client.post(
                "/extract",
                files={
                    "file": (
                        "invalid.txt",
                        b"Invalid UTF-8: \xff\xfe",
                        "text/plain",
                    )
                },
                data={"query": "Extract the text"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "Uploaded text document is not valid UTF-8."
    )
    assert len(temp_paths) == 1
    assert not Path(temp_paths[0]).exists()
