
import os
import tempfile
from pathlib import Path
from typing import Annotated
import uuid
import fitz

from document_reader.domain.validation import (
    ExtractionParsingError,
    ExtractionValidationError,
)

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile

from document_reader.config.settings import Settings
from document_reader.engine import DocumentEngine
from document_reader.extractors.llm import LLMExtractor
from document_reader.llm.openai import OpenAIClient
from document_reader.storage.json import JsonStorage
from fastapi.responses import JSONResponse

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".txt", ".pdf"}

class APIConfigurationError(RuntimeError):
    """Raised when the API cannot initialize its extraction engine."""

app = FastAPI(title="Doc-Keeper API", version="0.1.0")


@app.exception_handler(APIConfigurationError)
async def handle_api_configuration_error(request, exc):
    return JSONResponse(
        status_code=503,
        content={"detail": "Extraction service is not configured."},
    )


def create_engine() -> DocumentEngine:
    """Create an engine configured for real LLM-based extraction."""
    settings = Settings()
    if not settings.openai_api_key:
        raise APIConfigurationError(
            "Extraction service is not configured."
        )

    extractor = LLMExtractor(OpenAIClient(settings))
    return DocumentEngine(
        extractor=extractor,
        storage=JsonStorage(os.getenv("DOC_KEEPER_OUTPUT_DIR", "output")),
    )


def get_engine() -> DocumentEngine:
    """Dependency hook; override this in tests."""
    return create_engine()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/extract")
async def extract_document(
    file: Annotated[UploadFile, File()],
    query: Annotated[str, Form(min_length=1)],
    engine: Annotated[DocumentEngine, Depends(get_engine)],
) -> dict:
    filename = Path(file.filename or "").name
    extension = Path(filename).suffix.lower()

    if not filename or extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail="Unsupported file type. Upload a .txt or .pdf file.",
        )

    if not query.strip():
        raise HTTPException(status_code=422, detail="Query must not be blank.")

    temp_path: str | None = None

    try:
        size = 0
        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=extension, delete=False
        ) as temp_file:
            temp_path = temp_file.name

            while chunk := await file.read(64 * 1024):
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail="Uploaded file exceeds the 10 MiB limit.",
                    )
                temp_file.write(chunk)
            if size == 0:
                raise HTTPException(
                    status_code=422,
                    detail="Uploaded file must not be empty.",
                )

        request_id = uuid.uuid4().hex
        output_filename = f"{Path(filename).stem}-{request_id}{extension}"

        result = engine.process(
            temp_path,
            query,
            output_filename=output_filename,
        )

        response = {
            "filename": filename,
            "data": result["data"],
        }

        if "metadata" in result:
            response["metadata"] = result["metadata"]

        if "field_metadata" in result:
            response["field_metadata"] = result["field_metadata"]

        return response
    except HTTPException:
        raise
    except (ExtractionParsingError, ExtractionValidationError) as exc:
        raise HTTPException(
            status_code=422,
            detail="Extraction or validation failed.",
        ) from exc
    except (fitz.FileDataError, fitz.EmptyFileError) as exc:
        raise HTTPException(
            status_code=422,
            detail="Uploaded document is invalid or unreadable.",
        ) from exc
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=422,
            detail="Uploaded text document is not valid UTF-8.",
        ) from exc
    except APIConfigurationError as exc:
        raise HTTPException(
            status_code=503,
            detail="Extraction service is not configured.",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Document extraction failed.",
        ) from exc
    finally:
        await file.close()
        if temp_path is not None:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass
