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

Text and PDF reading, the extraction interface, an OpenAI-backed extractor, and optional schema validation are in place. `DocumentEngine` still uses `FakeExtractor` unless an `LLMExtractor` is supplied. There is no CLI or HTTP API yet.

```text
Phase 1 — Core Reader
        ✓

Phase 2 — Extraction Interface
        ✓

Phase 3 — First AI Extractor
        ✓

Phase 4 — Structured Extraction
        partial (schema validation on LLMExtractor)

Phase 5 — OCR
        ○

Phase 6 — Confidence & Validation
        ○

Phase 7 — Human Review
        ○

Phase 8 — API
        ○

Phase 9 — Async Processing
        ○

Phase 10 — Production Infrastructure
        ○
```

Phase 3 is usable by passing `LLMExtractor` into the engine. Phase 4 covers optional Pydantic schemas on `ExtractionRequest`. `DocumentEngine.process` accepts a query string and does not pass a schema.

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
