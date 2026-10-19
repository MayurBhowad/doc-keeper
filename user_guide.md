# User Guide — Document Reader AI

How to use Document Reader AI (doc-keeper) from Python.

There is no command-line interface or HTTP API yet. Calling the library is the supported way to run a document through the engine.

---

## What it does

You provide a `.txt` or `.pdf` file and a query. The engine reads the file, runs an extractor, writes a JSON file, and returns the extracted data.

The default extractor does not call a model. It echoes the query, filename, and document text. Pass `LLMExtractor` when you want OpenAI to extract fields from the text.

**Example:**

| Input | Extractor | Output `data` |
|-------|-----------|----------------|
| `invoice.txt` + “invoice number, vendor name, and total” | `FakeExtractor` (default) | `query`, `filename`, and the full document text |
| same inputs | `LLMExtractor` | JSON object returned by the model, for example `{ "invoice_number": "INV-123", "vendor_name": "ABC Pvt Ltd", "total": 15000 }` |

---

## Prerequisites

- Python 3.12 or newer
- Activate the project pyenv environment before installing or running
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

PDF reading uses PyMuPDF to extract embedded text. When a page contains fewer than the configured minimum number of text characters, the reader can use Tesseract OCR as a fallback. The default threshold is `1`, so OCR is invoked when a page has no extractable text.

---

## Supported document types

| Type | Status |
|------|--------|
| Plain text (`.txt`, UTF-8) | Supported |
| PDF (`.pdf`, embedded text and OCR fallback) | Supported |
| DOCX | Unsupported (`ValueError`) |
| Images / OCR | Standalone image files unsupported; OCR available for scanned PDF pages |

Extensions are matched in lowercase. A missing file raises `FileNotFoundError`.

---

## Basic usage

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
    "filename": "invoice.txt",lets update readme and user guide if needed
    "data": {
        "query": "Give me invoice number, vendor and total",
        "filename": "invoice.txt",
        "text": "...document text...",
    },
    "output": "output/invoice.json",
}
```

Choose another directory with `JsonStorage`:

```python
from document_reader.engine import DocumentEngine
from document_reader.storage.json import JsonStorage

engine = DocumentEngine(storage=JsonStorage("output"))
```

The saved file contains `filename` and `data`.

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

`result["data"]` is the JSON object parsed from the model response. The engine does not attach a schema on this path, so field names and types are whatever the model returns.

`LLMExtractor` accepts:

- a raw JSON object
- a JSON object wrapped in a Markdown code fence (` ```json ` or ` ``` `)
- a JSON object with surrounding text

The parsed value must be a JSON object.

---

## Structured extraction with schemas

Pass a Pydantic schema to `DocumentEngine.process()` to request structured extraction. The engine passes the schema to the extractor, and `LLMExtractor` validates the parsed response before returning it.

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

The returned `data` contains validated fields. The schema rejects unknown fields and enforces the declared types and constraints. Missing required fields and invalid values raise `ExtractionValidationError` after the configured extraction attempts are exhausted.

Schema validation is optional. Existing calls that omit `schema` retain their previous behavior. The default `FakeExtractor` does not perform LLM-based structured extraction; supply `LLMExtractor` to use a language model.

## Understanding results

### Engine return value

| Key | Meaning |
|-----|---------|
| `filename` | File name from the document |
| `data` | Extractor payload |
| `output` | Path of the written JSON file |

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
issue details.

### Errors

| Situation | Exception |
|-----------|-----------|
| File does not exist | `FileNotFoundError` |
| Extension is not `.txt` or `.pdf` | `ValueError` (`Unsupported document type`) |
| Model response has no JSON object, is invalid JSON, or is not an object | `ExtractionParsingError` |
| Schema is set and the object is missing fields, has extra fields, or has the wrong types | `ExtractionValidationError` |

Confidence scores and source-page metadata are supported through optional
`field_metadata`. The human-review workflow is available through `ReviewService`
and `ReviewJsonStorage`, described below. Review creation is explicit; extraction
does not automatically create review items or route them based on confidence.

---

## Human review workflow

Human review is available as a Python service. It is separate from
`DocumentEngine`, so existing extraction behavior and the legacy JSON output
remain unchanged.

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

## Configuration

Settings are read from the environment when `Settings()` is created.

| Variable | Required | Default |
|----------|----------|---------|
| `OPENAI_API_KEY` | Yes, for `OpenAIClient` | none |
| `OPENAI_MODEL` | No | `gpt-5.6-mini` |

`JsonStorage` defaults to the `output/` directory. Pass another path to its constructor to change that.

Keep API keys in the environment or a secret manager. Do not commit them.

---

## Troubleshooting

- **`ModuleNotFoundError: document_reader`** — run `pip install -e .` from the repository root, in the active environment.
- **Insufficient PDF text** — the reader attempts OCR when configured. Install `pytesseract`, `Pillow`, and the Tesseract executable if OCR dependencies are missing.
- **`Unsupported document type`** — use `.txt` or `.pdf`.
- **`ExtractionParsingError`** — the model response did not contain a JSON object.
- **`ExtractionValidationError`** — the JSON object did not match the schema passed on `ExtractionRequest`.
- **OpenAI authentication errors** — confirm `OPENAI_API_KEY` is set in the environment used to start Python. The library does not load a `.env` file.

---

## Related docs

- [README.md](README.md) — project overview and layout
- [PLAN.md](PLAN.md) — development roadmap
- [ARCHITECTURE.md](ARCHITECTURE.md) — system architecture
