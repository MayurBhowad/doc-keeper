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

PDF reading uses PyMuPDF and extracts embedded text. Scanned pages and images are not read.

---

## Supported document types

| Type | Status |
|------|--------|
| Plain text (`.txt`, UTF-8) | Supported |
| PDF (`.pdf`, embedded text) | Supported |
| DOCX | Unsupported (`ValueError`) |
| Images / OCR | Not available |

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

## Extraction requests

`DocumentEngine.process` takes two strings: a file path and a query. The query is sent to the extractor as written.

For schema-checked extraction, call `LLMExtractor` directly. Subclass `ExtractionSchema` and pass that class on `ExtractionRequest`. Unknown fields are rejected, and values must match the declared types.

```python
from pathlib import Path

from document_reader.config.settings import Settings
from document_reader.domain.document import Document
from document_reader.domain.extraction import ExtractionRequest
from document_reader.domain.schema import ExtractionSchema
from document_reader.extractors.llm import LLMExtractor
from document_reader.llm.openai import OpenAIClient
from document_reader.readers.registry import ReaderRegistry

class InvoiceExtraction(ExtractionSchema):
    invoice_number: str
    vendor_name: str
    total: float

document = Document(path=Path("documents/invoice.txt"))
reader = ReaderRegistry().get(document.extension)
content = reader.read(document)

extractor = LLMExtractor(OpenAIClient(Settings()))
result = extractor.extract(
    content,
    ExtractionRequest(
        query="Extract invoice details",
        schema=InvoiceExtraction,
    ),
)
```

The model is shown the schema and asked to return only those fields. The extractor then validates the parsed object. `result.data` is a dictionary of the validated fields.

This direct call does not write a JSON file. Use `JsonStorage` if you want the same file output as the engine:

```python
from document_reader.storage.json import JsonStorage

output_path = JsonStorage("output").save(content.filename, result)
```

---

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

### Errors

| Situation | Exception |
|-----------|-----------|
| File does not exist | `FileNotFoundError` |
| Extension is not `.txt` or `.pdf` | `ValueError` (`Unsupported document type`) |
| Model response has no JSON object, is invalid JSON, or is not an object | `ExtractionParsingError` |
| Schema is set and the object is missing fields, has extra fields, or has the wrong types | `ExtractionValidationError` |

Confidence scores, source pages, and review status are not part of the result yet.

---

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
- **Empty or missing PDF text** — the PDF reader returns embedded text only. Image-only pages stay empty until OCR exists.
- **`Unsupported document type`** — use `.txt` or `.pdf`.
- **`ExtractionParsingError`** — the model response did not contain a JSON object.
- **`ExtractionValidationError`** — the JSON object did not match the schema passed on `ExtractionRequest`.
- **OpenAI authentication errors** — confirm `OPENAI_API_KEY` is set in the environment used to start Python. The library does not load a `.env` file.

---

## Related docs

- [README.md](README.md) — project overview and layout
- [PLAN.md](PLAN.md) — development roadmap
- [ARCHITECTURE.md](ARCHITECTURE.md) — system architecture
