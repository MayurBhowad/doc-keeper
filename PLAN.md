# Doc-Keeper — Development Plan

## 1. Project Goal

Doc-Keeper is a developer-focused document processing engine for reading, extracting, understanding, validating, and storing information from documents.

The target workflow is:

```text
Document
   ↓
Read
   ↓
Understand request
   ↓
Extract information
   ↓
Validate
   ↓
Store result
```

Example:

```text
invoice.pdf

Request:
"Give me invoice number, vendor name and total."

Result:

{
  "invoice_number": "INV-123",
  "vendor_name": "ABC Pvt Ltd",
  "total": 15000
}
```

---

# 2. Development Principles

* Keep the system small and modular.
* Keep components independently testable.
* Prefer interfaces before implementations.
* Keep implementations replaceable.
* Develop locally first.
* Keep the core synchronous initially.
* Test every major feature.
* Make the system correct before optimizing it.
* Avoid infrastructure until there is an actual requirement.

Do not introduce prematurely:

* Microservices
* Kafka
* Redis
* Kubernetes
* Cloud infrastructure
* Vector databases
* RAG
* Agent frameworks
* Background queues

The first priority is the core document extraction engine.

---

# 3. Development Phases

## Phase 1 — Core Reader

**Status: COMPLETE**

Goal:

```text
TXT/PDF
   ↓
Reader
   ↓
DocumentContent
```

Completed:

* Project scaffolding
* Text reader
* PDF reader
* Document model
* DocumentContent model
* Reader abstraction
* ReaderRegistry
* JSON storage
* Initial engine
* Reader tests
* Domain tests
* Engine integration tests

Acceptance criteria:

* TXT files can be read.
* PDF files can be read.
* Missing files fail correctly.
* Unsupported files fail correctly.
* Tests pass.

---

# 4. Phase 2 — Extraction Interface

**Status: COMPLETE**

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

Completed:

* ExtractionRequest
* ExtractionResult
* DocumentExtractor interface
* FakeExtractor
* Engine integration
* JSON result storage
* Extractor tests
* Engine integration tests

Current flow:

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

Important:

No LLM has been introduced yet.

---

# 5. Phase 3 — First AI Extractor

**Status: VERIFIED**

The LLM extraction implementation is complete. `LLMExtractor` is integrated with the existing engine, and the API configures it as the production extractor.

`FakeExtractor` remains the default for `DocumentEngine` to preserve deterministic behavior for library users and tests.

**Goal:**

Introduce an LLM-backed extractor while preserving `FakeExtractor` as the default for deterministic library behavior.

**Target flow:**

```text
DocumentContent
      +
ExtractionRequest
      ↓
LLMExtractor
      ↓
ExtractionResult
```

**Tasks:**

- [x] Decide LLM provider
- [x] Define LLM configuration
- [x] Add configuration management
- [x] Implement LLM client
- [x] Create LLMExtractor
- [x] Send document content and extraction request to the LLM
- [x] Request structured output
- [x] Parse the LLM response
- [x] Handle invalid LLM responses
- [x] Handle API errors
- [x] Add mocked LLM tests
- [x] Keep FakeExtractor for deterministic tests
- [x] Configure LLMExtractor for production API requests
- [x] Update engine integration tests

**Acceptance example:**

```text
invoice.pdf

"Give me invoice number and total"

          ↓

    LLMExtractor

          ↓

{
  "invoice_number": "INV-123",
  "total": 15000
}
```

**Constraints:**

The existing architecture must remain intact.

Do not:

- Rewrite `DocumentEngine`.
- Remove `DocumentExtractor`.
- Remove `FakeExtractor`.
- Add RAG.
- Add vector databases.
- Add agents.
- Add queues.
- Add databases.
- Add unnecessary infrastructure.

The LLM implementation must remain replaceable.

---

# 6. Phase 4 — Structured Extraction

**Status: DONE**

Goal:

Make extraction reliable and schema-driven.

Tasks:

* [x] Introduce extraction schemas
* [x] Add Pydantic validation
* [x] Create a reusable InvoiceSchema example
* [x] Validate LLM output
* [x] Handle missing fields
* [x] Handle invalid values
* [x] Define schema errors
* [x] Add validation tests
* [x] Expose optional schemas through DocumentEngine
* [x] Add end-to-end engine schema validation tests

Example:

```text
InvoiceSchema

├── invoice_number
├── invoice_date
├── vendor_name
├── subtotal
├── tax
└── total
```

---

# 7. Phase 5 — OCR

**Status: COMPLETE**

Goal:

Support scanned and image-based documents.

Target flow:

```text
PDF
 ↓
Can text be extracted?
 │
 ├── YES → normal extraction
 │
 └── NO
       ↓
      OCR
       ↓
      Text
```

Tasks:

* [x] Detect insufficient PDF text
* [x] Add OCR support
* [x] Convert pages to images
* [x] Extract OCR text
* [x] Add OCR tests

---

# 8. Phase 6 — Confidence & Validation

**Status: COMPLETE**

Goal:

Make extracted information trustworthy.

Target flow:

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

* [x] Field confidence
* [x] Validation errors
* [x] Source page tracking
* [x] Basic business rules
* [x] Low-confidence detection

Example:

```json
{
  "field": "total",
  "value": 15000,
  "confidence": 0.91
}
```

---

# 9. Phase 7 — Human Review

**Status: VERIFIED**

Goal:

Allow humans to review and correct extraction results.

Implemented:

- [x] Review state (`pending`, `approved`, `rejected`)
- [x] Field corrections while a review is pending
- [x] Explicit approval and rejection
- [x] JSON persistence and reload of review records
- [x] Preserve original values separately from corrections
- [x] Validate review IDs and prevent sequential duplicate creation
- [x] Tests for state transitions, corrections, persistence, and invalid inputs

Scope and limitations:

- Review creation is explicit; confidence does not automatically route records.
- No UI, HTTP API, authentication, or automatic assignment.
- Concurrent duplicate creation is prevented by exclusive file creation; crash-safe writes are not guaranteed.

See `user_guide.md` for usage.

---

# 10. Phase 8 — API

**Status: INITIAL IMPLEMENTATION COMPLETE**

The initial HTTP API exposes the existing `DocumentEngine` through FastAPI.

Implemented endpoints:

- `GET /health` — returns the service health status.
- `POST /extract` — accepts `.txt` and `.pdf` multipart uploads and an
  extraction query, then returns extracted data and available metadata.

Implemented safeguards and behavior:

- Configures the OpenAI-backed extractor through environment settings.
- Limits uploads to 10 MiB and uses chunked reads.
- Uses unique output filenames for uploaded documents.
- Rejects unsupported extensions, empty uploads, and invalid requests.
- Returns consistent client errors without exposing extraction exception
  messages.
- Cleans up temporary upload files after success and failure.
- Preserves the existing `DocumentEngine` library interface.
- Includes endpoint tests that do not require live OpenAI requests.

Tasks:

- [x] Configure FastAPI
- [x] Create a separate API application module
- [x] Implement the health endpoint
- [x] Implement the extraction upload endpoint
- [x] Reuse the existing engine, readers, extractor, and storage
- [x] Configure the extractor through environment settings
- [x] Implement API error handling
- [x] Add API tests
- [x] Document local setup and endpoint usage

Out of scope for this initial implementation:

- Authentication and authorization
- Asynchronous processing
- Human-review management endpoints
- Production deployment and infrastructure configuration

Follow-up hardening may add stricter document validation, broader error
classification, and additional integration coverage.

---

# 11. Phase 9 — Async Processing

**Status: PLANNED**

Only introduce asynchronous processing when document processing time justifies it.

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

Potential technologies:

* Redis
* Celery
* RabbitMQ
* AWS SQS

Technology choice will be made when this phase becomes necessary.

---

# 12. Phase 10 — Production Infrastructure

**Status: PLANNED**

Only after the core product works.

Potential architecture:

```text
                 API
                  │
                  ▼
                Queue
                  │
                  ▼
                Worker
                  │
          ┌───────┼───────┐
          ▼       ▼       ▼
         S3    Database    AI
                  │
                  ▼
            Observability
```

Potential technologies:

* Docker
* PostgreSQL
* S3
* Redis/SQS
* Prometheus
* Grafana
* Loki

These are possibilities, not current requirements.

---

# 13. Current Milestone

The first two milestones are complete.

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

Phase 7 — Human Review
        ✓

Phase 8 — API
        ○

Phase 9 — Async Processing
        ○

Phase 10 — Production Infrastructure
        ○
```

The immediate objective is:

```text
TXT/PDF
   ↓
Reader
   ↓
DocumentContent
   ↓
LLMExtractor
   ↓
ExtractionResult
   ↓
JSON
```

---

# 14. Definition of Core Engine Complete

The core engine should eventually support:

```python
result = engine.process(
    document="documents/invoice.pdf",
    request="Give me invoice number, vendor and total"
)
```

And produce structured information such as:

```json
{
  "invoice_number": "INV-123",
  "vendor": "ABC Pvt Ltd",
  "total": 15000
}
```

---

# 15. Development Rules

### Rule 1 — One responsibility per component

```text
Reader      → reads
Extractor   → extracts
Storage     → stores
Engine      → orchestrates
```

### Rule 2 — Interfaces before implementations

If multiple implementations are expected, define the abstraction first.

### Rule 3 — Test every major component

Every phase must add appropriate tests.

### Rule 4 — Keep FakeExtractor

FakeExtractor must remain available for deterministic testing.

### Rule 5 — Keep implementations replaceable

The following should be replaceable without rewriting the engine:

```text
Reader
LLM
Extractor
Storage
OCR
```

### Rule 6 — Avoid premature infrastructure

Technology must solve an actual problem before being introduced.

### Rule 7 — Update this plan before major architectural changes

`PLAN.md` is the development roadmap and architectural decision checkpoint.
