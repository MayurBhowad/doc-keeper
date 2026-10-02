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

The core document-reading and extraction abstractions are in place. The next major milestone is integrating the first LLM-based extractor.

```text
Phase 1 — Core Reader
        ✓

Phase 2 — Extraction Interface
        ✓

Phase 3 — First AI Extractor
        ← CURRENT

Phase 4 — Structured Extraction
        ○

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

## Documentation

The project is documented in two primary files:

* **[PLAN.md](PLAN.md)** — Development roadmap, phases, milestones, acceptance criteria, and current progress.
* **[ARCHITECTURE.md](ARCHITECTURE.md)** — System architecture, components, responsibilities, data flow, interfaces, and architectural decisions.

Additional documentation:

* **[User Guide](user_guide.md)** — How to use Doc-Keeper.
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

The extraction layer is designed around an interface so different implementations can be introduced without rewriting the core engine.

Current:

```text
DocumentContent
      +
ExtractionRequest
      ↓
FakeExtractor
      ↓
ExtractionResult
```

Next:

```text
DocumentContent
      +
ExtractionRequest
      ↓
LLMExtractor
      ↓
ExtractionResult
```

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

This is why `FakeExtractor` remains part of the architecture even after introducing an LLM extractor.

### Local First

The early stages focus on running and testing the core engine locally.

Production infrastructure will be introduced only when the project actually requires it.

## Example Target Usage

Eventually, the core engine should support a workflow similar to:

```python
result = engine.process(
    document="documents/invoice.pdf",
    request="Give me invoice number, vendor and total"
)
```

Producing structured information such as:

```json
{
  "invoice_number": "INV-123",
  "vendor": "ABC Pvt Ltd",
  "total": 15000
}
```

## Development

Run the test suite with:

```bash
pytest
```

The exact development commands may evolve as the project grows.

## Roadmap

The complete development roadmap is maintained in:

**[PLAN.md](PLAN.md)**

The complete system architecture is maintained in:

**[ARCHITECTURE.md](ARCHITECTURE.md)**

These two files should be updated whenever major development or architectural decisions are made.

## License

See the repository for the current licensing information.
