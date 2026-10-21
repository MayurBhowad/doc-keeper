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
initial HTTP API does not expose review-management endpoints.


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

## Project Structure

```text
doc-keeper/
│
├── src/
│   └── document_reader/
│
├── tests/
│
├── documents/
│
├── output/
│
├── README.md
├── PLAN.md
├── ARCHITECTURE.md
├── user_guide.md
├── requirements.txt
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

## Current Usage

With the package installed, the engine reads a `.txt` or `.pdf` file, runs the default extractor, and writes JSON under `output/`:

```python
from document_reader.engine import DocumentEngine

engine = DocumentEngine()
result = engine.process(
    "documents/invoice.txt",
    "Give me invoice number, vendor and total",
)
```

`FakeExtractor` returns the query, filename, and document text. It does not call a model.

To extract with OpenAI, pass `LLMExtractor` explicitly. Set `OPENAI_API_KEY` in the environment. See the [User Guide](user_guide.md).

## HTTP API

The initial HTTP API exposes document extraction through FastAPI.

### Configuration

Install the project dependencies:

```bash
pip install -r requirements.txt
pip install -e .
```

Configure the OpenAI API key and, optionally, the model and output directory:

```bash
export OPENAI_API_KEY="your-api-key"
export OPENAI_MODEL="gpt-5.6-mini"
export DOC_KEEPER_OUTPUT_DIR="output"
```

Start the local development server:

```bash
uvicorn document_reader.api:app --reload
```

The API is available at `http://127.0.0.1:8000`. Interactive API documentation
is available at `/docs`.

### Health check

```bash
curl http://127.0.0.1:8000/health
```

Example response:

```json
{"status": "ok"}
```

### Extract from a document

Send a multipart request containing a `.txt` or `.pdf` file and a query:

```bash
curl -X POST http://127.0.0.1:8000/extract \
  -F "file=@invoice.pdf" \
  -F "query=Extract invoice number, vendor name, and total"
```

The response contains the original filename, extracted `data`, and any
available `metadata` or `field_metadata`. The API does not return the server's
storage path. Results are also saved by the configured JSON storage component.

Uploads are limited to 10 MiB. Unsupported extensions return HTTP 415; missing
fields, empty uploads, unreadable documents, and extraction-validation failures
return HTTP 422. Unexpected extraction failures return HTTP 500 with a generic
error message. The initial API does not include authentication, asynchronous
processing, or human-review endpoints.

The API uses the existing `DocumentEngine` and configures an
`LLMExtractor`; API tests use fake extractors and do not require live OpenAI
requests.

## Development

Python 3.12 or newer is required.

```bash
pip install -r requirements.txt
pip install -e .
pytest
```

## Roadmap

The complete development roadmap is maintained in:

**[PLAN.md](PLAN.md)**

The complete system architecture is maintained in:

**[ARCHITECTURE.md](ARCHITECTURE.md)**

These two files should be updated whenever major development or architectural decisions are made.

## License

See the repository for the current licensing information.
