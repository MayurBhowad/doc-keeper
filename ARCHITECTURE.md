# Doc-Keeper — Architecture

## 1. Overview

Doc-Keeper is a modular document processing engine.

Its responsibility is to transform:

```text
Document
   +
User Request
   ↓
Structured Information
```

The initial architecture is intentionally simple and synchronous.

---

# 2. Core Architecture

```text
                         Document
                            │
                            ▼
                    ┌───────────────┐
                    │    Reader     │
                    └───────┬───────┘
                            │
                            ▼
                    DocumentContent
                            │
                            │
                  ExtractionRequest
                            │
                            ▼
                    ┌───────────────┐
                    │   Extractor   │
                    └───────┬───────┘
                            │
                            ▼
                    ExtractionResult
                            │
                            ▼
                    ┌───────────────┐
                    │    Storage    │
                    └───────┬───────┘
                            │
                            ▼
                           JSON
```

The central orchestrator is:

```text
DocumentEngine
```

---

# 3. Architectural Layers

## 3.1 Domain

Contains the core models and concepts.

```text
domain/
├── document.py
├── content.py
└── extraction.py
```

Responsibilities:

* Represent documents.
* Represent extracted document content.
* Represent extraction requests.
* Represent extraction results.

The domain layer should remain independent of:

* LLM providers
* HTTP frameworks
* Databases
* Cloud services
* Infrastructure

---

# 4. Document

Represents the input document.

Conceptually:

```python
Document(
    path="documents/invoice.pdf"
)
```

The Document model should contain document-level information only.

It should not:

* Read the file.
* Call an LLM.
* Extract fields.
* Store results.

---

# 5. DocumentContent

Represents content extracted from a document.

Initial model:

```python
DocumentContent(
    filename="invoice.pdf",
    document_type="pdf",
    text="..."
)
```

Future possibilities:

```text
DocumentContent
├── metadata
├── pages
├── text
├── blocks
├── tables
├── images
└── coordinates
```

The initial model should remain small.

---

# 6. Reader Layer

Readers convert documents into `DocumentContent`.

```text
read(Document)
      ↓
DocumentContent
```

Architecture:

```text
Reader
├── TextReader
└── PDFReader
```

Future:

```text
Reader
├── TextReader
├── PDFReader
├── DocxReader
├── ImageReader
└── OCRReader
```

### Reader responsibility

A reader may:

* Open a document.
* Read its contents.
* Extract raw text.
* Create DocumentContent.

A reader must not:

* Call an LLM.
* Extract business fields.
* Validate business rules.
* Store extraction results.

---

# 7. Reader Abstraction

The engine should depend on the reader abstraction rather than a concrete reader.

Conceptually:

```text
DocumentEngine
      ↓
Reader
      ↓
TextReader / PDFReader / ...
```

This allows readers to be replaced without changing the engine.

---

# 8. Reader Registry

`ReaderRegistry` determines which reader should handle a document.

Conceptually:

```text
Document
   ↓
ReaderRegistry
   ↓
┌───────────────┐
│               │
TXT             PDF
│               │
▼               ▼
TextReader   PDFReader
```

Future readers can be registered without changing the engine workflow.

---

# 9. Extraction Layer

The extractor is responsible for answering the user's request using document content.

Input:

```text
DocumentContent
+
ExtractionRequest
```

Output:

```text
ExtractionResult
```

Architecture:

```text
Extractor
├── FakeExtractor
├── LLMExtractor
├── RuleExtractor
└── VisionExtractor
```

Not all implementations need to exist immediately.

---

# 10. ExtractionRequest

Represents what the user wants to extract.

Initial form:

```python
ExtractionRequest(
    query="Give me invoice number and total"
)
```

Future form:

```python
ExtractionRequest(
    fields=[
        "invoice_number",
        "vendor_name",
        "total"
    ]
)
```

The request belongs to the domain rather than the LLM implementation.

---

# 11. DocumentExtractor Interface

The engine should depend on an abstraction.

Conceptually:

```text
DocumentExtractor
        │
        ├── FakeExtractor
        ├── LLMExtractor
        ├── RuleExtractor
        └── VisionExtractor
```

This provides two important properties:

1. Deterministic testing through `FakeExtractor`.
2. Replaceable AI implementations.

---

# 12. FakeExtractor

`FakeExtractor` exists primarily for testing.

It should remain available after introducing the LLM.

Example:

```text
DocumentContent
      +
ExtractionRequest
      ↓
FakeExtractor
      ↓
Known ExtractionResult
```

This allows engine tests to run without:

* API calls
* Network access
* LLM cost
* nondeterministic output

---

# 13. LLMExtractor

`LLMExtractor` is the first AI implementation.

Target:

```text
DocumentContent
       +
ExtractionRequest
       ↓
   LLMExtractor
       ↓
ExtractionResult
```

The LLMExtractor is responsible for:

* Preparing the extraction input.
* Sending it to the configured LLM.
* Requesting structured output.
* Parsing the response.
* Converting the response into `ExtractionResult`.
* Handling LLM/API failures.

It should not own:

* Document reading.
* File management.
* Application orchestration.
* Persistence.
* Business-specific workflow.

---

# 14. LLM Provider Abstraction

The application should avoid tightly coupling the extractor to one provider.

Conceptually:

```text
LLMExtractor
      ↓
LLM Client Interface
      ↓
┌───────────────┐
│               │
Provider A   Provider B
```

The provider can therefore be changed without changing the overall extraction architecture.

The exact provider is a Phase 3 implementation decision.

---

# 15. Storage Layer

Storage persists extraction results.

Current implementation:

```text
JsonStorage
```

Future:

```text
Storage
├── JsonStorage
├── DatabaseStorage
└── S3Storage
```

Storage receives results and persists them.

It must not:

* Read documents.
* Call an LLM.
* Perform extraction.
* Perform business validation.

---

# 16. DocumentEngine

`DocumentEngine` is the orchestration layer.

Conceptually:

```python
engine.process(
    document,
    request
)
```

Internally:

```text
process()
   │
   ├── Reader.read()
   │
   ├── Extractor.extract()
   │
   └── Storage.save()
```

The engine owns the workflow.

Individual components own their individual responsibilities.

---

# 17. End-to-End Flow

Current architecture:

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

Current extractor:

```text
FakeExtractor
```

Next extractor:

```text
LLMExtractor
```

---

# 18. Target AI Flow

After Phase 3:

```text
PDF/TXT
   ↓
Reader
   ↓
DocumentContent
   ↓
ExtractionRequest
   ↓
LLMExtractor
   ↓
LLM Client
   ↓
Structured Response
   ↓
ExtractionResult
   ↓
JSON
```

The important architectural rule is that adding AI should **not require rewriting the document reader or engine**.

---

# 19. Future Validation Layer

Validation will eventually sit between extraction and persistence.

```text
LLMExtractor
      ↓
ExtractionResult
      ↓
Schema Validation
      ↓
Business Validation
      ↓
Storage
```

Example:

```text
Invoice
├── invoice_number
├── vendor_name
├── subtotal
├── tax
└── total
```

Pydantic can be introduced when structured extraction becomes the next requirement.

---

# 20. Future OCR Architecture

For scanned documents:

```text
Document
   ↓
PDF/Image Reader
   ↓
Text Available?
   │
   ├── YES ──────────────┐
   │                     │
   └── NO                │
       ↓                 │
      OCR                │
       ↓                 │
      Text ──────────────┘
             ↓
        DocumentContent
```

OCR should remain replaceable like other infrastructure components.

---

# 21. Future Human Review

Eventually:

```text
Extraction
    ↓
Validation
    ↓
Confidence
    ↓
 ┌───────────────┐
 │               │
High            Low
 │               │
 ▼               ▼
Approve       Human Review
```

Human review should operate on the extraction result rather than becoming part of the reader or extractor implementation.

---

# 22. Future API

Only after the core engine is stable:

```text
Client
  ↓
FastAPI
  ↓
DocumentEngine
```

The API should be a thin application layer around the existing engine.

The core engine should remain usable without the API.

---

# 23. Future Async Architecture

If document processing eventually becomes long-running:

```text
Client
  ↓
API
  ↓
Queue
  ↓
Worker
  ↓
DocumentEngine
  ↓
Storage
```

The queue should be introduced only when synchronous processing is no longer sufficient.

---

# 24. Future Production Architecture

A possible production architecture:

```text
                    Client
                      │
                      ▼
                     API
                      │
                      ▼
                    Queue
                      │
                      ▼
                    Worker
                      │
               ┌──────┼──────┐
               ▼      ▼      ▼
              S3    Database  AI
                      │
                      ▼
                Observability
```

Potential technologies:

```text
API          → FastAPI
Database     → PostgreSQL
Object Store → S3
Queue        → Redis/SQS
Metrics      → Prometheus
Dashboards   → Grafana
Logs         → Loki
```

These are future options, not current dependencies.

---

# 25. Dependency Direction

The desired dependency direction is:

```text
Application
     ↓
Engine
     ↓
Interfaces
     ↓
Implementations
```

For example:

```text
DocumentEngine
      ↓
DocumentExtractor
      ↓
LLMExtractor
      ↓
LLM Provider
```

The engine should not directly depend on a specific LLM provider.

Similarly:

```text
DocumentEngine
      ↓
Reader
      ↓
PDFReader
```

rather than:

```text
DocumentEngine
      ↓
PDFReader
```

---

# 26. Project Structure

Target structure:

```text
doc-keeper/
│
├── src/
│   └── document_reader/
│       │
│       ├── domain/
│       │   ├── document.py
│       │   ├── content.py
│       │   └── extraction.py
│       │
│       ├── readers/
│       │   ├── base.py
│       │   ├── text.py
│       │   ├── pdf.py
│       │   └── registry.py
│       │
│       ├── extractors/
│       │   ├── base.py
│       │   ├── fake.py
│       │   └── llm.py
│       │
│       ├── storage/
│       │   └── json.py
│       │
│       └── engine.py
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

The actual implementation may evolve as features are added.

---

# 27. Architectural Rules

### Rule 1 — One responsibility per component

```text
Reader      → reads
Extractor   → extracts
Storage     → stores
Engine      → orchestrates
```

### Rule 2 — Interfaces before implementations

Expected multiple implementations should have an abstraction.

### Rule 3 — Keep components replaceable

The following should be replaceable independently:

```text
Reader
Extractor
LLM Provider
Storage
OCR
```

### Rule 4 — Keep the core synchronous initially

No queue or worker until there is a real requirement.

### Rule 5 — Keep the core local-first

The initial development environment should require only:

```text
Python
pytest
```

plus the dependencies required by the current phase.

### Rule 6 — Keep infrastructure outside the core domain

Cloud services, queues, databases, and providers should not leak into domain models.

### Rule 7 — Test boundaries

Tests should verify:

```text
Domain
Reader
Extractor
Storage
Engine
```

independently and through integration tests.

---

# 28. Architecture Decision Summary

| Decision   | Choice                         |
| ---------- | ------------------------------ |
| Core style | Modular monolith               |
| Processing | Synchronous initially          |
| Domain     | Framework-independent          |
| Reader     | Interface + implementations    |
| Extraction | Interface + implementations    |
| AI         | Replaceable LLM implementation |
| Testing    | Unit + integration             |
| Storage    | JSON initially                 |
| API        | Deferred                       |
| Queue      | Deferred                       |
| Database   | Deferred                       |
| RAG        | Deferred                       |
| Vector DB  | Deferred                       |
| Agents     | Deferred                       |
| Cloud      | Deferred                       |

The architecture is intentionally designed to become more capable without becoming more complicated before the complexity is justified.
