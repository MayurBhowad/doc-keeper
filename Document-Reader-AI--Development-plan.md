# Document Reader AI

A small developer-focused Document Reader and AI Extraction engine.

The goal is to build the core document-processing engine first, then progressively introduce AI, OCR, validation, APIs, and production infrastructure.

---

## 1. Project Goal

Build a system that can:

```text
Document
   ↓
Read document
   ↓
Understand requested information
   ↓
Extract information
   ↓
Validate result
   ↓
Store result
```

Initial example:

```text
invoice.pdf

User:
"Give me the invoice number, vendor name and total."

System:
{
  "invoice_number": "INV-123",
  "vendor_name": "ABC Pvt Ltd",
  "total": 15000
}
```

---

# 2. Development Philosophy

Keep the system:

* Small
* Testable
* Modular
* Easy to understand
* Easy to replace components
* Local-first during development

Do NOT introduce infrastructure before it is necessary.

Avoid premature:

* Microservices
* Kafka
* Redis
* Kubernetes
* AWS
* Databases
* Complex agent frameworks
* Vector databases
* RAG

The first priority is making the **core extraction engine work correctly**.

---

# 3. Current Architecture

```text
                    Document
                       │
                       ▼
                ┌─────────────┐
                │   Reader    │
                └──────┬──────┘
                       │
                       ▼
                DocumentContent
                       │
                       │
             User Extraction Request
                       │
                       ▼
                ┌─────────────┐
                │  Extractor  │
                └──────┬──────┘
                       │
                       ▼
                ExtractionResult
                       │
                       ▼
                ┌─────────────┐
                │   Storage   │
                └─────────────┘
                       │
                       ▼
                     JSON
```

The central orchestrator is:

```text
DocumentEngine
```

---

# 4. Component Responsibilities

## Reader

Responsible only for reading documents.

Input:

```text
Document
```

Output:

```text
DocumentContent
```

Readers:

```text
Reader
├── TextReader
└── PdfReader
```

Future:

```text
├── DocxReader
├── ImageReader
└── OCRReader
```

Reader must NOT:

* Call an LLM
* Extract business fields
* Validate invoice totals
* Store results

---

## DocumentContent

Represents the content extracted from a document.

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

Keep the initial model small.

---

## Extractor

Responsible for extracting information requested by the user.

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

Example:

```text
Request:

"Give me invoice number and total."
```

Result:

```json
{
  "invoice_number": "INV-123",
  "total": 15000
}
```

Future implementations:

```text
Extractor
├── FakeExtractor
├── LLMExtractor
├── RuleExtractor
└── VisionExtractor
```

---

## ExtractionRequest

Represents what the user wants from the document.

Initial version:

```python
ExtractionRequest(
    query="Give me invoice number and total"
)
```

Later:

```python
ExtractionRequest(
    fields=[
        "invoice_number",
        "vendor_name",
        "total"
    ]
)
```

---

## ExtractionResult

Represents the extracted information.

Initial version:

```python
ExtractionResult(
    data={
        "invoice_number": "INV-123",
        "total": 15000
    }
)
```

Future:

```text
ExtractionResult
├── data
├── confidence
├── source_pages
├── source_coordinates
├── validation_errors
└── metadata
```

---

## Storage

Responsible only for persistence.

Initial:

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

Storage must NOT:

* Read documents
* Call the LLM
* Perform extraction
* Validate business rules

---

# 5. Engine

`DocumentEngine` coordinates the system.

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

Individual components own their own responsibilities.

---

# 6. Project Structure

Target structure:

```text
document-reader/
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
│       │   └── pdf.py
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
├── documents/
│
├── output/
│
├── tests/
│   ├── test_readers.py
│   ├── test_extractors.py
│   └── test_engine.py
│
├── PLAN.md
├── README.md
└── requirements.txt
```

---

# 7. Development Phases

## Phase 1 — Core Reader

Goal:

```text
TXT/PDF
   ↓
Reader
   ↓
DocumentContent
```

Tasks:

* [x] Create project
* [x] Create basic text reader
* [x] Create basic PDF reader
* [x] Create basic storage
* [x] Create initial engine
* [x] Add basic tests
* [ ] Refactor readers into separate classes
* [ ] Create `Document` model
* [ ] Create `DocumentContent` model

Acceptance criteria:

```text
TXT can be read.
PDF can be read.
Missing files fail correctly.
Unsupported files fail correctly.
Tests pass.
```

---

# Phase 2 — Extraction Interface

Goal:

```text
DocumentContent
      +
ExtractionRequest
      ↓
Extractor
      ↓
ExtractionResult
```

Tasks:

* [ ] Create `ExtractionRequest`
* [ ] Create `ExtractionResult`
* [ ] Create `Extractor` interface
* [ ] Create `FakeExtractor`
* [ ] Integrate extractor with engine
* [ ] Add extractor tests
* [ ] Add engine integration tests

Acceptance criteria:

```text
Document
   ↓
Reader
   ↓
DocumentContent
   ↓
FakeExtractor
   ↓
ExtractionResult
   ↓
JSON
```

No LLM yet.

---

# Phase 3 — First AI Extractor

Goal:

Replace:

```text
FakeExtractor
```

with:

```text
LLMExtractor
```

Tasks:

* [ ] Choose LLM provider
* [ ] Add configuration
* [ ] Implement LLM client
* [ ] Send document content + user request
* [ ] Parse structured response
* [ ] Handle invalid responses
* [ ] Add tests with mocked LLM responses

Acceptance criteria:

```text
invoice.pdf
+
"Give me invoice number and total"
        ↓
LLMExtractor
        ↓
structured JSON
```

---

# Phase 4 — Structured Extraction

Goal:

Make extraction reliable rather than returning arbitrary JSON.

Tasks:

* [ ] Introduce extraction schemas
* [ ] Add Pydantic validation
* [ ] Create `InvoiceSchema`
* [ ] Validate LLM output
* [ ] Handle missing fields
* [ ] Handle invalid values

Example:

```text
Invoice
├── invoice_number
├── invoice_date
├── vendor_name
├── subtotal
├── tax
└── total
```

---

# Phase 5 — OCR

Goal:

Support scanned/image-based documents.

Pipeline:

```text
PDF
 ↓
Can text be extracted?
 ├── YES → normal extraction
 │
 └── NO
      ↓
     OCR
      ↓
     Text
```

Tasks:

* [ ] Detect empty/insufficient PDF text
* [ ] Add OCR
* [ ] Convert page images
* [ ] Extract OCR text
* [ ] Add OCR tests

---

# Phase 6 — Confidence & Validation

Goal:

Make extraction trustworthy.

Pipeline:

```text
LLM
 ↓
Schema Validation
 ↓
Business Validation
 ↓
Confidence
 ↓
Result
```

Tasks:

* [ ] Field confidence
* [ ] Validation errors
* [ ] Source page tracking
* [ ] Basic business rules
* [ ] Low-confidence detection

Example:

```json
{
  "field": "total",
  "value": 15000,
  "confidence": 0.91
}
```

---

# Phase 7 — Human Review

Goal:

Allow humans to correct uncertain extraction.

```text
Extraction
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

Tasks:

* [ ] Review state
* [ ] Editable extracted values
* [ ] Approve/reject
* [ ] Store corrections

---

# Phase 8 — API

Only after the core engine is stable.

```text
Client
  ↓
FastAPI
  ↓
DocumentEngine
```

Tasks:

* [ ] Upload endpoint
* [ ] Processing endpoint
* [ ] Result endpoint
* [ ] Error handling
* [ ] API tests

---

# Phase 9 — Async Processing

Only when documents take long enough to require background processing.

Potential architecture:

```text
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

Possible technologies:

```text
Redis
Celery
RabbitMQ
SQS
```

Do not introduce these before they are needed.

---

# Phase 10 — Production Infrastructure

Only after the core product works.

Potential components:

```text
                    API
                     │
                     ▼
                    Queue
                     │
                     ▼
                   Worker
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
         S3       Database      AI
                     │
                     ▼
               Observability
```

Potential technologies:

```text
Docker
PostgreSQL
S3
Redis/SQS
Prometheus
Grafana
Loki
```

---

# 8. First Target

The immediate target is intentionally small:

```text
TXT/PDF
   ↓
Reader
   ↓
DocumentContent
   ↓
FakeExtractor
   ↓
ExtractionResult
   ↓
JSON
```

Once this works:

```text
FakeExtractor
      ↓
LLMExtractor
```

That becomes our first actual AI extraction system.

---

# 9. Rules for Development

### Rule 1 — Keep the core synchronous initially

No queues or background workers until required.

### Rule 2 — One responsibility per component

Reader reads.

Extractor extracts.

Storage stores.

Engine orchestrates.

### Rule 3 — Interfaces before implementations

If we expect multiple implementations, define the interface first.

### Rule 4 — Test every major component

Every phase should have tests.

### Rule 5 — Don't optimize prematurely

Make it correct first.

### Rule 6 — Don't add infrastructure because it is available

Technology should solve an actual problem.

### Rule 7 — Prefer replaceable components

We should be able to replace:

```text
PDF reader
LLM
Storage
OCR
```

without rewriting the engine.

### Rule 8 — Keep the first version local

The developer version should run on the laptop with:

```bash
python
pytest
```

---

# 10. Definition of "Core Engine Complete"

The core engine is considered complete when this works:

```python
result = engine.process(
    document="documents/invoice.pdf",
    request="Give me invoice number, vendor and total"
)
```

and produces:

```json
{
  "invoice_number": "INV-123",
  "vendor": "ABC Pvt Ltd",
  "total": 15000
}
```

with tests covering:

* document reading
* unsupported documents
* missing documents
* extraction
* invalid extraction
* storage
* engine integration

---

# 11. Current Status

**Current phase: Phase 1 — Core Reader**

Completed:

```text
[x] Project created
[x] Text reading
[x] PDF reading
[x] JSON storage
[x] Basic engine
[x] Basic tests
```

Current:

```text
→ Refactor Reader architecture
→ Introduce domain objects
```

Next:

```text
Phase 2 — Extraction Interface
```

---

# 12. Current Architecture Decision

For now:

```text
Document
   ↓
Reader
   ↓
DocumentContent
   ↓
Extractor
   ↓
ExtractionResult
   ↓
Storage
```

Do not deviate from this architecture without first updating this `PLAN.md`.

When a major architectural decision changes, update this document.

---

# 13. Long-Term Vision

The eventual system should become:

```text
                     Document AI
                         │
            ┌────────────┴────────────┐
            │                         │
         Document                  User Request
            │                         │
            ▼                         ▼
         Reader                   Extraction
            │                         │
            ▼                         ▼
       DocumentContent ────────► AI Engine
                                  │
                          ┌───────┴────────┐
                          │                │
                     Validation        Confidence
                          │                │
                          └───────┬────────┘
                                  ▼
                              Result
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
                 Storage                   Human Review
```

The system should eventually support:

```text
PDF
DOCX
Images
Scanned documents
Invoices
Receipts
Purchase Orders
Bank Statements
Contracts
Resumes
Custom documents
```

while keeping the same fundamental engine architecture.
