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

**Status: NEXT**

This is the current development target.

Goal:

Replace:

```text
FakeExtractor
```

with:

```text
LLMExtractor
```

Target flow:

```text
DocumentContent
      +
ExtractionRequest
      ↓
LLMExtractor
      ↓
ExtractionResult
```

Tasks:

* [ ] Decide LLM provider
* [ ] Define LLM configuration
* [ ] Add configuration management
* [ ] Implement LLM client
* [ ] Create LLMExtractor
* [ ] Send document content and extraction request to the LLM
* [ ] Request structured output
* [ ] Parse the LLM response
* [ ] Handle invalid LLM responses
* [ ] Handle API errors
* [ ] Add mocked LLM tests
* [ ] Keep FakeExtractor for deterministic tests
* [ ] Make LLMExtractor the default production extractor
* [ ] Update engine integration tests

Acceptance example:

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

### Constraints

The existing architecture must remain intact.

Do not:

* Rewrite DocumentEngine.
* Remove DocumentExtractor.
* Remove FakeExtractor.
* Add RAG.
* Add vector databases.
* Add agents.
* Add queues.
* Add databases.
* Add unnecessary infrastructure.

The LLM implementation must remain replaceable.

---

# 6. Phase 4 — Structured Extraction

**Status: PLANNED**

Goal:

Make extraction reliable and schema-driven.

Tasks:

* [ ] Introduce extraction schemas
* [ ] Add Pydantic validation
* [ ] Create InvoiceSchema
* [ ] Validate LLM output
* [ ] Handle missing fields
* [ ] Handle invalid values
* [ ] Define schema errors
* [ ] Add validation tests

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

**Status: PLANNED**

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

* [ ] Detect insufficient PDF text
* [ ] Add OCR support
* [ ] Convert pages to images
* [ ] Extract OCR text
* [ ] Add OCR tests

---

# 8. Phase 6 — Confidence & Validation

**Status: PLANNED**

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

# 9. Phase 7 — Human Review

**Status: PLANNED**

Goal:

Allow humans to review and correct uncertain extraction.

Flow:

```text
Extraction
    ↓
Confidence
    ↓
 ┌───────────────┐
 │               │
High            Low
 │               │
 ↓               ↓
Approve       Human Review
```

Tasks:

* [ ] Review state
* [ ] Editable extracted values
* [ ] Approve/reject
* [ ] Store corrections

---

# 10. Phase 8 — API

**Status: PLANNED**

Only after the core engine is stable.

Target:

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
