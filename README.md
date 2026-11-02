# Doc-Keeper

Doc-Keeper is a developer-focused document processing engine designed to read documents, understand extraction requests, extract structured information, validate results, and store the output.

The core idea is:

```text
Document
   ↓
Read
   ↓
Understand Request
   ↓
Extract
   ↓
Validate
   ↓
Store
```

## Project Status

Doc-Keeper is currently being developed incrementally.

Text and PDF reading, an OpenAI-backed extractor, optional schema validation,
field-level confidence metadata, source-page attribution, configurable
business-rule validation, a Python-based human-review workflow, and an initial
FastAPI extraction API are implemented. `DocumentEngine` still uses
`FakeExtractor` unless an `LLMExtractor` is supplied. The HTTP API configures
the OpenAI-backed extractor from environment settings. Confidence scores and
page attribution are model-reported estimates and are not independently
verified. Human review is explicitly initiated through `ReviewService`; the
initial HTTP API does not expose review-management endpoints. There is no
command-line interface.

```text
Phase 1 — Core Reader
        ✓

Phase 2 — Extraction Interface
        ✓

Phase 3 — First AI Extractor
        ✓

Phase 4 — Structured Extraction
        ✓

Phase 5 — OCR
        ✓

Phase 6 — Confidence & Validation
        ✓

Phase 7 — Human Review (implemented)
        ✓

Phase 8 — API
        ✓

Phase 9 — Async Processing
        ○

Phase 10 — Production Infrastructure
        ○
```

Phase 6 adds optional `field_metadata` to extraction results. Each field can include a `confidence` estimate and `source_pages` list. Schema validation and configured business rules run before storage; validation failures can expose structured issues. Legacy plain-JSON LLM responses remain supported.

Phase 3 is usable by passing `LLMExtractor` into the engine. Phase 4 supports optional Pydantic schemas through `DocumentEngine.process(path, query, schema=InvoiceSchema)`. The schema guides extraction and validates the parsed result before storage.

## Getting Started

The fastest way to see the whole pipeline work is to run the HTTP API locally
and upload a document. The steps below assume a Linux or macOS shell, run from
the repository root.

### 1. Set up the Python environment

Python 3.12 or newer is required. Use the project virtual environment in `.venv`:

```bash
source .venv/bin/activate
python --version
```

`.venv/` is git-ignored, so a fresh clone does not include it. Create it first
if it is missing:

```bash
python3.12 -m venv .venv
source .venv/bin/activate## Getting Started

The fastest way to see the whole pipeline work is to run the HTTP API locally
and upload a document. The steps below assume a Linux or macOS shell, run from
the repository root.
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
pip install -e .
```

`requirements.txt` pins the runtime and test dependencies (including FastAPI,
Uvicorn, PyMuPDF, and the OpenAI SDK). `pip install -e .` installs the
`document_reader` package from `src/` in editable mode.

OCR for scanned PDFs needs extra, optional dependencies. See
[Optional OCR setup](user_guide.md#optional-ocr-setup).

### 3. Configure the environment

The API reads its settings from environment variables. Set them in the same
shell that will start the server:

```bash
read -rs OPENAI_API_KEY && export OPENAI_API_KEY   # paste the key; input is hidden
export OPENAI_MODEL="gpt-5.6-mini"                 # optional, this is the default
export DOC_KEEPER_OUTPUT_DIR="output"              # optional, this is the default
```

| Variable | Required | Default | Used for |
|----------|----------|---------|----------|
| `OPENAI_API_KEY` | Yes, for the API's default `openai` provider | none | Authenticating to OpenAI |
| `OPENAI_MODEL` | No | `gpt-5.6-mini` | Model used for extraction |
| `DOC_KEEPER_OUTPUT_DIR` | No | `output` | Directory where the API writes result JSON |

The code also reads `LLM_PROVIDER` (default `openai`). Set it to `ollama` to use
a local Ollama server instead; see the
[User Guide configuration](user_guide.md#configuration).

Doc-Keeper does not load `.env` files. Keep keys in the environment or a secret
manager, and never commit them.

### 4. Start the API server

```bash
uvicorn document_reader.api:app --reload
```

Uvicorn listens on `http://127.0.0.1:8000` by default. The API has no
authentication, so keep it bound to localhost during local use.

### 5. Check that the server is running

```bash
curl http://127.0.0.1:8000/health
```

```json
{"status": "ok"}
```

`/health` only confirms that the server is up. It does not check the LLM
configuration. A missing `OPENAI_API_KEY` is reported by `/extract` as HTTP 503.

### 6. Explore the API in Swagger UI

Open `http://127.0.0.1:8000/docs` in a browser. FastAPI generates this page from
the code:

1. Expand **POST /extract** and select **Try it out**.
2. Choose a `.txt` or `.pdf` file for `file`.
3. Enter an extraction request in `query`.
4. Select **Execute** and inspect the response body and status code.

### 7. Run your first extraction

Create a small sample document. `documents/` is git-ignored local data:

```bash
mkdir -p documents
cat > documents/invoice.txt <<'EOF'
Invoice Number: INV-123
Vendor: ABC Pvt Ltd
Total: 15000
EOF
```

Upload it with a query:

```bash
curl -sS -X POST http://127.0.0.1:8000/extract \
  -F "file=@documents/invoice.txt" \
  -F "query=Extract invoice number, vendor name, and total" \
  | python -m json.tool
```

PDFs work the same way, for example with `-F "file=@documents/invoice.pdf"`.

The document text is sent to the configured LLM provider. Only upload documents
you are permitted to share with that provider.

### 8. Understand the response

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
    "invoice_number": {"confidence": 0.98, "source_pages": [1]}
  }
}
```

| Field | Meaning |
|-------|---------|
| `filename` | Base name of the uploaded file |
| `data` | Fields extracted by the model. The API does not apply a schema, so field names and types depend on the query and the model |
| `metadata` | Extractor run details: `attempts` (the extractor retries once if the response cannot be parsed or validated), `duration_ms`, and `model` |
| `field_metadata` | Optional, model-reported `confidence` (0.0–1.0) and 1-based `source_pages` per field. Omitted when the model provides none |

Confidence scores and page numbers are model-reported estimates. They are not
independently verified.

### 9. Find the stored output

Each successful request also writes a JSON file to `DOC_KEEPER_OUTPUT_DIR`
(default `output/`, relative to the directory where Uvicorn was started). The
directory is created if needed.

```bash
ls -t output/ | head -n 5
python -m json.tool output/invoice-<request-id>.json
```

Files are named `<original-name>-<request-id>.json`, where `<request-id>` is a
random 32-character hex value, so repeated uploads of the same file do not
overwrite each other. The stored file contains `filename` (the generated name,
for example `invoice-<request-id>.txt`), `data`, and `field_metadata` when
present. It does not include `metadata`. The API response does not reveal the
server's storage path. `output/` is git-ignored because it can contain extracted
document data.

### API limits and errors

Uploads are limited to 10 MiB. Unsupported extensions return HTTP 415; missing
fields, empty uploads, unreadable documents, and extraction-validation failures
return HTTP 422. Oversized uploads return HTTP 413, and a missing LLM
configuration returns HTTP 503. Unexpected extraction failures return HTTP 500
with a generic error message. The initial API does not include authentication,
asynchronous processing, or human-review endpoints. The full status-code table
is in the [User Guide](user_guide.md#status-codes-and-errors).

### Which extractor runs where

- **HTTP API:** `/extract` always builds a `DocumentEngine` with `LLMExtractor`
  and the LLM client selected by `LLM_PROVIDER` (OpenAI by default).
- **Python library:** `DocumentEngine()` defaults to `FakeExtractor`, which
  returns the query, filename, and document text without calling a model. Pass
  `LLMExtractor` explicitly to use a model. See
  [Python library usage](#python-library-usage).

API tests use fake extractors and do not require live OpenAI requests.

## Documentation

The project is documented in two primary files:

* **[PLAN.md](PLAN.md)** — Development roadmap, phases, milestones, acceptance criteria, and current progress.
* **[ARCHITECTURE.md](ARCHITECTURE.md)** — System architecture, components, responsibilities, data flow, interfaces, and architectural decisions.

Additional documentation:

* **[User Guide](user_guide.md)** — How to use Doc-Keeper.
* **[Evaluation Guide](evaluation_guide.md)** — Evaluate extraction results against expected outputs.
* **[Requirements](requirements.txt)** — Python dependencies.

## Current Architecture

```text
                    Document
                       │
                       ▼
                ReaderRegistry
                       │
                       ▼
                    Reader
                       │
                       ▼
               DocumentContent
                       │
                       │
              ExtractionRequest
                       │
                       ▼
                   Extractor
                       │
                       ▼
              ExtractionResult
                       │
                       ▼
                   Storage
                       │
                       ▼
                     JSON
```

The extraction layer is an interface, so implementations can be swapped without rewriting the engine.

Default engine path:

```text
DocumentContent
      +
ExtractionRequest
      ↓
FakeExtractor
      ↓
ExtractionResult
```

Optional AI path:

```text
DocumentContent
      +
ExtractionRequest
      ↓
LLMExtractor
      ↓
ExtractionResult
```

When the request includes a schema, `LLMExtractor` asks the model for those fields and validates the parsed JSON before returning it.

### How an API request moves through the pipeline

| Step | Component | What happens in `POST /extract` |
|------|-----------|----------------------------------|
| Receive | `document_reader.api` | Checks the extension, streams the upload to a temporary file, and enforces the 10 MiB limit |
| Read | `ReaderRegistry` → `TextReader` / `PDFReader` | Produces `DocumentContent` with the text and per-page text |
| Understand request | `ExtractionRequest` | Wraps the `query` (the API does not pass a schema) |
| Extract | `LLMExtractor` + LLM client | Builds a prompt with page-numbered text, calls the model, and parses the JSON response |
| Validate | `LLMExtractor` | Checks the JSON object and field metadata, retrying once on failure |
| Store | `JsonStorage` | Writes `<name>-<request-id>.json` to `DOC_KEEPER_OUTPUT_DIR` |
| Respond | `document_reader.api` | Returns `filename`, `data`, `metadata`, and `field_metadata`, then deletes the temporary file |

## Project Structure

```text
doc-keeper/
│
├── src/
│   └── document_reader/
│
├── tests/
│
├── documents/          (local input files, git-ignored)
│
├── output/             (extraction results, git-ignored)
│
├── README.md
├── PLAN.md
├── ARCHITECTURE.md
├── user_guide.md
├── evaluation_guide.md
├── requirements.txt
├── pyproject.toml
└── .gitignore
```

## Development Philosophy

Doc-Keeper is being built incrementally.

The project intentionally avoids introducing infrastructure before it is required.

For example, the initial implementation does not require:

* Microservices
* Kafka
* Redis
* Kubernetes
* Vector databases
* RAG
* Agent frameworks
* Cloud infrastructure

The focus is first on building a clean, testable document-processing core.

## Core Design Principles

### Modular

Each component has a focused responsibility.

```text
Reader      → reads documents
Extractor   → extracts information
Storage     → stores results
Engine      → orchestrates the workflow
```

### Replaceable

Important implementations should be replaceable without rewriting the core engine.

```text
Reader
Extractor
LLM Provider
Storage
OCR
```

### Testable

The system should be testable without requiring external AI services.

This is why `FakeExtractor` remains the engine default and stays available after the LLM extractor.

### Local First

The early stages focus on running and testing the core engine locally.

Production infrastructure will be introduced only when the project actually requires it.

## Python Library Usage

The HTTP API is a thin layer over `DocumentEngine`, which can also be called
directly from Python. With the package installed, the engine reads a `.txt` or
`.pdf` file, runs the default extractor, and writes JSON under `output/`:

```python
from document_reader.engine import DocumentEngine

engine = DocumentEngine()
result = engine.process(
    "documents/invoice.txt",
    "Give me invoice number, vendor and total",
)
```

`FakeExtractor` returns the query, filename, and document text. It does not call a model.

To extract with OpenAI, pass `LLMExtractor` explicitly. Set `OPENAI_API_KEY` in the environment. Unlike the API, the library writes to `JsonStorage`'s default `output/` directory and does not read `DOC_KEEPER_OUTPUT_DIR`; pass `JsonStorage("path")` to change it. Schemas, business rules, and human review are available only from Python. See the [User Guide](user_guide.md).

## Development

Python 3.12 or newer is required.

```bash
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
pytest
```

The test suite does not call live LLM services.

## Roadmap

The complete development roadmap is maintained in:

**[PLAN.md](PLAN.md)**

The complete system architecture is maintained in:

**[ARCHITECTURE.md](ARCHITECTURE.md)**

These two files should be updated whenever major development or architectural decisions are made.

## License

See the repository for the current licensing information.
