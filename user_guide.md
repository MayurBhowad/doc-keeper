# User Guide — Document Reader AI

How to use Document Reader AI (doc-keeper) through its HTTP API and from Python.

Doc-Keeper has two supported interfaces:

- **HTTP API** (FastAPI): upload a `.txt` or `.pdf` file with a query to `POST /extract`. This is the quickest way to try the full pipeline.
- **Python library**: call `DocumentEngine` directly. This also exposes schemas, business rules, and the human-review workflow.

There is no command-line interface.

---

## Implemented and planned functionality

| Capability | Status |
|------------|--------|
| Text (`.txt`, UTF-8) and PDF reading, OCR fallback for scanned PDF pages | Implemented |
| `FakeExtractor` (default for `DocumentEngine`) and `LLMExtractor` | Implemented |
| OpenAI client (default) and Ollama client, selected by `LLM_PROVIDER` | Implemented |
| Optional Pydantic schema validation | Implemented (Python only) |
| Field confidence and source-page metadata | Implemented (model-reported) |
| Business-rule validation (`positive` rule) | Implemented (Python only) |
| Human review (`ReviewService`, `ReviewJsonStorage`) | Implemented (Python only) |
| HTTP API: `GET /health`, `POST /extract` | Implemented |
| API authentication | Not implemented |
| Schemas, business rules, or review endpoints in the API | Not implemented |
| Asynchronous processing (Phase 9) | Planned |
| Production infrastructure (Phase 10) | Planned |

See [PLAN.md](PLAN.md) for the roadmap.

---

## What it does

You provide a `.txt` or `.pdf` file and a query. The engine reads the file, runs an extractor, writes a JSON file, and returns the extracted data.

The default extractor does not call a model. It echoes the query, filename, and document text. Pass `LLMExtractor` when you want OpenAI to extract fields from the text. The HTTP API always uses `LLMExtractor`.

**Example:**

| Input | Extractor | Output `data` |
|-------|-----------|----------------|
| `invoice.txt` + “invoice number, vendor name, and total” | `FakeExtractor` (Python default) | `query`, `filename`, and the full document text |
| same inputs | `LLMExtractor` (Python opt-in, always used by the API) | JSON object returned by the model, for example `{ "invoice_number": "INV-123", "vendor_name": "ABC Pvt Ltd", "total": 15000 }` |

---

## Prerequisites

- Python 3.12 or newer
- The project virtual environment in `.venv`, activated before installing or running:

```bash
source .venv/bin/activate
```

`.venv/` is git-ignored. If it does not exist, create it with `python3.12 -m venv .venv` and activate it.

- Dependencies and the local package:

```bash
pip install -r requirements.txt
pip install -e .
```

`pip install -e .` makes `document_reader` importable. The library lives under `src/`.

### Optional OCR setup

OCR requires the Tesseract system executable and two Python packages.

On Ubuntu:

```bash
sudo apt install tesseract-ocr
```

In the active project virtual environment:

```bash
pip install pytesseract Pillow
```

The default reader registry configures Tesseract OCR for PDFs. These dependencies are optional for ordinary PDFs with extractable embedded text; they are not required for every PDF, and are only needed when OCR is actually invoked.

To configure a different text threshold, instantiate the reader with `PDFReader(ocr=TesseractOCR(), min_text_chars=20)`. This invokes OCR when a page contains fewer than 20 extractable text characters.

PDF reading uses PyMuPDF to extract embedded text. When a page contains fewer than the configured minimum number of text characters, the reader can use Tesseract OCR as a fallback. The default threshold is `1`, so OCR is invoked when a page has no extractable text. Pages with no text and no images or drawings are treated as empty and skip OCR.

---

## Supported document types

| Type | Status |
|------|--------|
| Plain text (`.txt`, UTF-8) | Supported |
| PDF (`.pdf`, embedded text and OCR fallback) | Supported |
| DOCX | Unsupported (`ValueError` in Python, HTTP 415 in the API) |
| Images / OCR | Standalone image files unsupported; OCR available for scanned PDF pages |

Extensions are matched in lowercase. A missing file raises `FileNotFoundError`.

---

## Using the HTTP API

### 1. Configure the environment

Set the variables in the shell that will start the server. The server reads them from its own process environment, so restart it after changing them.

```bash
source .venv/bin/activate
read -rs OPENAI_API_KEY && export OPENAI_API_KEY   # paste the key; input is hidden
export OPENAI_MODEL="gpt-5.6-mini"                 # optional, default
export DOC_KEEPER_OUTPUT_DIR="output"              # optional, default
```

See [Configuration](#configuration) for all variables, including the Ollama option.

### 2. Start the server

```bash
uvicorn document_reader.api:app --reload
```

The server listens on `http://127.0.0.1:8000`. The API has no authentication, so do not expose it on a shared network.

### 3. Check health

```bash
curl http://127.0.0.1:8000/health
```

```json
{"status": "ok"}
```

This only confirms the server is running. LLM configuration is checked when `/extract` is called.

### 4. Upload a document with a query

Create a sample document (`documents/` is git-ignored):

```bash
mkdir -p documents
cat > documents/invoice.txt <<'EOF'
Invoice Number: INV-123
Vendor: ABC Pvt Ltd
Total: 15000
EOF
```

Send it as `multipart/form-data` with two required fields, `file` and `query`:

```bash
curl -sS -X POST http://127.0.0.1:8000/extract \
  -F "file=@documents/invoice.txt" \
  -F "query=Extract invoice number, vendor name, and total" \
  | python -m json.tool
```

The query is free text. It controls which fields the model returns and how they are named. For a PDF, use `-F "file=@documents/invoice.pdf"`.

To see the HTTP status code alongside the body, use `curl -sS -i ...` without the `json.tool` pipe.

You can also send the same request from Swagger UI at `http://127.0.0.1:8000/docs`: expand **POST /extract**, select **Try it out**, choose a file, enter a query, and select **Execute**.

The document text is sent to the configured LLM provider. Only upload documents you are permitted to share with that provider.

### 5. Inspect the JSON response

Example response (values depend on the document and the model):

```json
{
  "filename": "invoice.txt",
  "data": {
    "invoice_number": "INV-123",
    "vendor_name": "ABC Pvt Ltd",
    "total": 15000
  },
  "metadata": {
    "attempts": 1,
    "duration_ms": 2140,
    "model": "gpt-5.6-mini"
  },
  "field_metadata": {
    "invoice_number": {"confidence": 0.98, "source_pages": [1]},
    "total": {"confidence": 0.62, "source_pages": [1]}
  }
}
```

| Field | Meaning |
|-------|---------|
| `filename` | Base name of the uploaded file |
| `data` | Extracted values. The API does not apply a schema or business rules, so names and types are whatever the model returns |
| `metadata.attempts` | Number of model calls. `LLMExtractor` retries once when a response cannot be parsed or validated |
| `metadata.duration_ms` | Extraction time in milliseconds |
| `metadata.model` | Model name from the configured client |
| `field_metadata` | Optional per-field `confidence` (0.0–1.0) and 1-based `source_pages`. Omitted when the model returns no metadata |

Text files are presented to the model as a single page, so `source_pages` for a `.txt` upload is `[1]` when present. Treat missing metadata as unknown, not as zero confidence.

### 6. Find the stored output

Each successful request writes one JSON file to `DOC_KEEPER_OUTPUT_DIR` (default `output/`, relative to the directory where Uvicorn was started). The directory is created if needed.

```bash
ls -t output/ | head -n 5
python -m json.tool output/invoice-<request-id>.json
```

- File name: `<original-name>-<request-id>.json`, where `<request-id>` is a random 32-character hex value. Repeated uploads do not overwrite each other.
- Contents: `filename` (the generated name, for example `invoice-<request-id>.txt`), `data`, and `field_metadata` when present. `metadata` is not stored.
- The API response does not reveal the storage path.
- The uploaded file is written to a temporary file for processing and deleted after the request, whether it succeeds or fails.

Output files contain extracted document data. `output/` is git-ignored; do not commit its contents.

### What happens during an `/extract` request

1. **Configure:** before the endpoint runs, FastAPI checks that `file` and `query` are present and calls `get_engine()`. `create_engine()` reads `Settings()`, selects the OpenAI or Ollama client from `LLM_PROVIDER`, and builds `DocumentEngine` with `LLMExtractor` and `JsonStorage(DOC_KEEPER_OUTPUT_DIR)`. A new engine is created for each request.
2. **Receive:** the API rejects extensions other than `.txt` and `.pdf`, rejects blank queries, and streams the upload to a temporary file while enforcing the 10 MiB limit.
3. **Read:** `ReaderRegistry` selects `TextReader` or `PDFReader`, which returns `DocumentContent` with the full text and per-page text.
4. **Understand request:** the query is wrapped in an `ExtractionRequest` without a schema.
5. **Extract:** `LLMExtractor` sends a prompt containing the page-numbered text and the query, and asks for a `doc-keeper-extraction-v1` JSON envelope with `data` and `field_metadata`.
6. **Validate:** the response must be a JSON object, and any field metadata must reference extracted fields and use valid confidence and page values. On failure, the extractor retries once with the error added to the prompt.
7. **Store:** `JsonStorage` writes the result file.
8. **Respond:** the API returns `filename`, `data`, `metadata`, and `field_metadata` (when present), then removes the temporary file.

### Status codes and errors

Error responses have the form `{"detail": "..."}`. Internal error details are not returned; unexpected failures are logged by the server.

| Status | `detail` | Cause |
|--------|----------|-------|
| 400 | `Invalid Content-Length header.` | Malformed `Content-Length` request header |
| 413 | `Uploaded file exceeds the 10 MiB limit.` | File larger than 10 MiB |
| 413 | `Request body exceeds the permitted size.` | Whole request body larger than 11 MiB |
| 415 | `Unsupported file type. Upload a .txt or .pdf file.` | Missing filename or unsupported extension |
| 422 | Validation details from FastAPI | Missing `file` or `query`, or an empty `query` |
| 422 | `Query must not be blank.` | Query contains only whitespace |
| 422 | `Uploaded file must not be empty.` | Zero-byte upload |
| 422 | `Uploaded document is invalid or unreadable.` | Corrupt or unreadable PDF |
| 422 | `Uploaded text document is not valid UTF-8.` | `.txt` file is not UTF-8 |
| 422 | `Extraction or validation failed.` | Model response could not be parsed or validated after retrying |
| 503 | `Extraction service is not configured.` | `OPENAI_API_KEY` missing for the `openai` provider, or unsupported `LLM_PROVIDER` |
| 500 | `Document extraction failed.` | Any other failure, for example LLM provider errors, missing OCR dependencies for a scanned PDF, or storage errors |

---

## Using the Python library

### Default engine

`DocumentEngine` uses `FakeExtractor` and writes JSON to `output/`.

```python
from document_reader.engine import DocumentEngine

engine = DocumentEngine()
result = engine.process(
    "documents/invoice.txt",
    "Give me invoice number, vendor and total",
)
```

`result` has this shape:

```python
{
    "filename": "invoice.txt",
    "data": {
        "query": "Give me invoice number, vendor and total",
        "filename": "invoice.txt",
        "text": "...document text...",
    },
    "output": "output/invoice.json",
}
```

The library names output files after the document (`invoice.txt` → `invoice.json`), so processing the same file again overwrites the previous result. This differs from the API, which adds a request ID.

Choose another directory with `JsonStorage`:

```python
from document_reader.engine import DocumentEngine
from document_reader.storage.json import JsonStorage

engine = DocumentEngine(storage=JsonStorage("output"))
```

The saved file contains `filename` and `data`, plus `field_metadata` when present. `DOC_KEEPER_OUTPUT_DIR` is read only by the HTTP API, not by `JsonStorage`.

### OpenAI extraction

Set `OPENAI_API_KEY` in the environment. Do not put the key in source files. `OPENAI_MODEL` is optional and defaults to `gpt-5.6-mini`.

```python
from document_reader.config.settings import Settings
from document_reader.engine import DocumentEngine
from document_reader.extractors.llm import LLMExtractor
from document_reader.llm.openai import OpenAIClient
from document_reader.storage.json import JsonStorage

engine = DocumentEngine(
    extractor=LLMExtractor(OpenAIClient(Settings())),
    storage=JsonStorage("output"),
)

result = engine.process(
    "documents/invoice.txt",
    "Give me invoice number, vendor and total",
)
```

`result["data"]` is the JSON object parsed from the model response. The engine does not attach a schema on this path, so field names and types are whatever the model returns. `result["metadata"]` contains `attempts`, `duration_ms`, and `model`.

`LLMExtractor` accepts:

- a raw JSON object
- a JSON object wrapped in a Markdown code fence (` ```json ` or ` ``` `)
- a JSON object with surrounding text

The parsed value must be a JSON object. By default `LLMExtractor` makes up to two attempts (`max_attempts=2`).

---

## Structured extraction with schemas

Pass a Pydantic schema to `DocumentEngine.process()` to request structured extraction. The engine passes the schema to the extractor, and `LLMExtractor` validates the parsed response before returning it. Schemas are not available through the HTTP API.

Define a reusable invoice schema:

```python
from pydantic import Field

from document_reader.domain.schema import ExtractionSchema


class InvoiceSchema(ExtractionSchema):
    invoice_number: str
    vendor_name: str
    total: int = Field(gt=0)
```

Use it with the engine:

```python
from document_reader.config.settings import Settings
from document_reader.engine import DocumentEngine
from document_reader.extractors.llm import LLMExtractor
from document_reader.llm.openai import OpenAIClient
from document_reader.storage.json import JsonStorage

engine = DocumentEngine(
    extractor=LLMExtractor(OpenAIClient(Settings())),
    storage=JsonStorage("output"),
)

result = engine.process(
    "documents/invoice.txt",
    "Extract invoice number, vendor name, and total",
    schema=InvoiceSchema,
)

print(result["data"])
print(result["output"])
```

The returned `data` contains validated fields. The schema rejects unknown fields and enforces the declared types and constraints. `ExtractionSchema` uses Pydantic strict mode, so values are not coerced; for example, `"15000"` is rejected for an `int` field. Missing required fields and invalid values raise `ExtractionValidationError` after the configured extraction attempts are exhausted.

Schema validation is optional. Existing calls that omit `schema` retain their previous behavior. The default `FakeExtractor` does not perform LLM-based structured extraction; supply `LLMExtractor` to use a language model.

## Understanding results

### Engine return value

| Key | Meaning |
|-----|---------|
| `filename` | File name from the document |
| `data` | Extractor payload |
| `output` | Path of the written JSON file |
| `metadata` | Extractor run details; present when the extractor provides them (`LLMExtractor` does, `FakeExtractor` does not) |
| `field_metadata` | Per-field confidence and source pages; present only when available |

### Stored JSON

```json
{
  "filename": "invoice.txt",
  "data": {}
}
```

`data` depends on the extractor. `FakeExtractor` always includes `query`, `filename`, and `text`. `LLMExtractor` returns the parsed object, or the validated object when a schema was provided.

### Field confidence and source pages

`LLMExtractor` supports an optional response envelope containing `data` and
`field_metadata`. Each metadata entry can include a confidence estimate and
1-based source page numbers:

```json
{
  "filename": "invoice.pdf",
  "data": {
    "invoice_number": "INV-123",
    "total": 15000
  },
  "field_metadata": {
    "invoice_number": {
      "confidence": 0.98,
      "source_pages": [1]
    },
    "total": {
      "confidence": 0.62,
      "source_pages": [2]
    }
  }
}
```

The saved JSON includes `field_metadata` only when metadata is present.
Legacy plain-JSON model responses continue to work and produce no field metadata.

Confidence values are model-reported estimates, not calibrated probabilities.
Page attribution is also model-reported and is not independently verified.
Missing metadata should be treated as unknown, not as zero confidence.

Use `FieldMetadata.is_low_confidence()` to check a score against a threshold:

```python
from document_reader.domain.extraction import FieldMetadata

metadata = FieldMetadata(confidence=0.62, source_pages=(2,))
print(metadata.is_low_confidence(threshold=0.7))  # True
```

The default threshold is `0.5`. A field without a confidence value is never reported as low confidence.

### Business-rule validation

Business rules are optional. Configure a `BusinessValidator` when constructing
the engine to reject extracted values that violate those rules before storage:

```python
from document_reader.domain.validator import BusinessRule, BusinessValidator
from document_reader.engine import DocumentEngine

engine = DocumentEngine(
    business_validator=BusinessValidator(
        rules=[BusinessRule(field="total", rule="positive")]
    )
)
```

The built-in `positive` rule requires a finite numeric value greater than zero.
A violation raises `ExtractionValidationError`, which exposes structured issues
through its `issues` attribute. Schema validation errors also provide structured
issue details. A missing field also fails the rule. Business rules are not
applied by the HTTP API.

### Errors

| Situation | Exception |
|-----------|-----------|
| File does not exist | `FileNotFoundError` |
| Extension is not `.txt` or `.pdf` | `ValueError` (`Unsupported document type`) |
| Scanned PDF page needs OCR but OCR dependencies are missing | `RuntimeError` |
| Model response has no JSON object, is invalid JSON, or is not an object | `ExtractionParsingError` |
| Schema is set and the object is missing fields, has extra fields, or has the wrong types | `ExtractionValidationError` |
| A configured business rule fails | `ExtractionValidationError` |

Confidence scores and source-page metadata are supported through optional
`field_metadata`. The human-review workflow is available through `ReviewService`
and `ReviewJsonStorage`, described below. Review creation is explicit; extraction
does not automatically create review items or route them based on confidence.

---

## Human review workflow

Human review is available as a Python service. It is separate from
`DocumentEngine`, so existing extraction behavior and the legacy JSON output
remain unchanged. There are no review endpoints in the HTTP API.

A review record contains:

- `pending`, `approved`, or `rejected` status
- Original extracted values
- Corrected values stored separately
- Effective values, where corrections override original values
- Available field confidence and source-page metadata

Create a review explicitly from an `ExtractionResult`:

```python
from document_reader.domain.extraction import ExtractionResult, FieldMetadata
from document_reader.services.review import ReviewService
from document_reader.storage.review_json import ReviewJsonStorage

storage = ReviewJsonStorage("output/reviews")
reviews = ReviewService(storage)

extraction = ExtractionResult(
    data={"invoice_number": "INV-123", "total": 15000},
    field_metadata={
        "total": FieldMetadata(confidence=0.62, source_pages=(2,))
    },
)

record = reviews.create("invoice-123", extraction)
print(record.status.value)  # pending

# Correct a field, then approve the record.
record = reviews.correct("invoice-123", "total", 15500)
print(record.effective_data)  # total is 15500; original remains 15000

record = reviews.approve("invoice-123")

# Reload the persisted record.
record = reviews.get("invoice-123")
print(record.status.value)       # approved
print(record.extraction.data)    # original extracted values
print(record.effective_data)     # values with corrections applied
```

Reviews are saved as `output/reviews/<review_id>.json`. Review IDs may contain only letters, digits, `.`, `_`, and `-`. Notes:

- `create()` does not overwrite an existing review. Running the example twice raises `FileExistsError`; delete the file or use a new ID.
- Only `pending` reviews can be corrected, approved, or rejected (`reviews.reject(review_id)`). Changing a finished review raises `ValueError`.
- Corrections must name a field present in the original extracted data.

---

## Configuration

Settings are read from the environment when `Settings()` is created.

| Variable | Required | Default | Read by |
|----------|----------|---------|---------|
| `LLM_PROVIDER` | No | `openai` | HTTP API (`openai` or `ollama`) |
| `OPENAI_API_KEY` | Yes, for `OpenAIClient` and the API's `openai` provider | none | `Settings` |
| `OPENAI_MODEL` | No | `gpt-5.6-mini` | `Settings` |
| `OLLAMA_BASE_URL` | No | `http://localhost:11434` | `Settings`, used when `LLM_PROVIDER=ollama` |
| `OLLAMA_MODEL` | No | `llama3:latest` | `Settings`, used when `LLM_PROVIDER=ollama` |
| `DOC_KEEPER_OUTPUT_DIR` | No | `output` | HTTP API only |

`JsonStorage` defaults to the `output/` directory. Pass another path to its constructor to change that.

Keep API keys in the environment or a secret manager. Do not commit them.

---

## Limitations

- **No API authentication.** Anyone who can reach the server can upload documents and spend LLM quota. Run it on `127.0.0.1` only.
- **No asynchronous processing.** Each `/extract` request is handled synchronously and returns only after reading, extraction, and storage finish. There are no job IDs, queues, or status endpoints (planned for Phase 9).
- **API scope.** The API accepts one `.txt` or `.pdf` file (up to 10 MiB) and a free-text query. It does not accept schemas, apply business rules, or manage reviews.
- **Model-reported metadata.** Confidence scores and source pages are not independently verified.
- **Local JSON storage only.** Results and reviews are plain JSON files on local disk.
- **No `.env` loading.** Environment variables must be exported in the shell that runs Python or Uvicorn.

---

## Troubleshooting

- **`ModuleNotFoundError: document_reader`** — activate `.venv` and run `pip install -e .` from the repository root.
- **API returns 503 `Extraction service is not configured.`** — export `OPENAI_API_KEY` (or set `LLM_PROVIDER=ollama`) and restart Uvicorn.
- **API returns 500 `Document extraction failed.`** — check the Uvicorn console log for the error, such as provider authentication, network, or OCR dependency failures.
- **Insufficient PDF text** — the reader attempts OCR when configured. Install `pytesseract`, `Pillow`, and the Tesseract executable if OCR dependencies are missing.
- **`Unsupported document type`** or HTTP 415 — use `.txt` or `.pdf`.
- **`ExtractionParsingError`** — the model response did not contain a JSON object.
- **`ExtractionValidationError`** — the JSON object did not match the schema passed to `DocumentEngine.process()`, or a business rule failed.
- **OpenAI authentication errors** — confirm `OPENAI_API_KEY` is set in the environment used to start Python. The library does not load a `.env` file.

---

## Related docs

- [README.md](README.md) — project overview, getting started, and layout
- [PLAN.md](PLAN.md) — development roadmap
- [ARCHITECTURE.md](ARCHITECTURE.md) — system architecture
- [evaluation_guide.md](evaluation_guide.md) — evaluating extraction results
