
import os
import tempfile
from pathlib import Path
from typing import Annotated
import uuid
import fitz
import logging

from document_reader.domain.validation import (
    ExtractionParsingError,
    ExtractionValidationError,
)

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile

from document_reader.config.settings import Settings
from document_reader.engine import DocumentEngine
from document_reader.extractors.llm import LLMExtractor
from document_reader.llm.openai import OpenAIClient
from document_reader.llm.ollama import OllamaClient
from document_reader.storage.json import JsonStorage
from fastapi.responses import JSONResponse

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".txt", ".pdf"}

class APIConfigurationError(RuntimeError):
    """Raised when the API cannot initialize its extraction engine."""

class RequestBodyLimitMiddleware:
    """Reject requests whose body exceeds the configured size limit."""

    def __init__(self, app, max_body_bytes: int) -> None:
        self.app = app
        self.max_body_bytes = max_body_bytes

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        content_length = next(
            (
                value.decode("latin-1")
                for name, value in scope["headers"]
                if name.lower() == b"content-length"
            ),
            None,
        )

        if content_length is not None:
            try:
                declared_length = int(content_length)
            except ValueError:
                await self._reject(send, 400, "Invalid Content-Length header.")
                return

            if declared_length < 0:
                await self._reject(send, 400, "Invalid Content-Length header.")
                return

            if declared_length > self.max_body_bytes:
                await self._reject(
                    send,
                    413,
                    "Request body exceeds the permitted size.",
                )
                return

        received_bytes = 0
        response_started = False

        async def limited_receive():
            nonlocal received_bytes
            message = await receive()

            if message["type"] == "http.request":
                received_bytes += len(message.get("body", b""))

                if received_bytes > self.max_body_bytes:
                    raise RequestBodyTooLarge

            return message

        async def tracked_send(message):
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, tracked_send)
        except RequestBodyTooLarge:
            if response_started:
                raise

            await self._reject(
                send,
                413,
                "Request body exceeds the permitted size.",
            )

    @staticmethod
    async def _reject(send, status_code: int, detail: str) -> None:
        import json

        body = json.dumps({"detail": detail}).encode("utf-8")
        await send(
            {
                "type": "http.response.start",
                "status": status_code,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode("ascii")),
                ],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": body,
            }
        )


class RequestBodyTooLarge(Exception):
    """Raised when a streamed request body exceeds the limit."""


MAX_REQUEST_BODY_SIZE = MAX_UPLOAD_BYTES + 1024 * 1024

app = FastAPI(title="Doc-Keeper API", version="0.1.0")
app.add_middleware(
    RequestBodyLimitMiddleware,
    max_body_bytes=MAX_REQUEST_BODY_SIZE,
)


@app.exception_handler(APIConfigurationError)
async def handle_api_configuration_error(request, exc):
    return JSONResponse(
        status_code=503,
        content={"detail": "Extraction service is not configured."},
    )



def create_engine() -> DocumentEngine:
    """Create an engine configured for the selected LLM provider."""
    settings = Settings()

    if settings.llm_provider == "ollama":
        llm_client = OllamaClient(settings)
    elif settings.llm_provider == "openai":
        if not settings.openai_api_key:
            raise APIConfigurationError(
                "Extraction service is not configured."
            )
        llm_client = OpenAIClient(settings)
    else:
        raise APIConfigurationError(
            f"Unsupported LLM provider: {settings.llm_provider}"
        )

    extractor = LLMExtractor(llm_client)
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
        logging.getLogger(__name__).exception(
            "Document extraction failed"
        )
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
