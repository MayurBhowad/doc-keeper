# User Guide — Document Reader AI

How to use Document Reader AI (doc-keeper) once features are available.

> This guide will be populated as the project grows. Sections marked **Coming soon** are placeholders.

---

## What it does

You provide a document and describe what information you need. The system reads the document, extracts the requested fields, validates them when possible, and returns structured results (typically JSON).

**Example (planned):**

| Input | Output |
|-------|--------|
| `invoice.pdf` + “invoice number, vendor name, and total” | `{ "invoice_number": "INV-123", "vendor_name": "ABC Pvt Ltd", "total": 15000 }` |

---

## Prerequisites

**Coming soon** — runtime, Python version, and environment setup.

- Python (version TBD)
- Activate the project pyenv environment before installing or running
- Dependencies: `pip install -r requirements.txt`

---

## Supported document types

| Type | Status |
|------|--------|
| Plain text | Planned |
| PDF | Planned |
| DOCX | Future |
| Images / OCR | Future |

---

## Basic usage

**Coming soon** — CLI, library API, or HTTP endpoints will be documented here when implemented.

### Planned flow

1. Provide a document path (or upload)
2. Specify the fields or question to extract
3. Receive a structured extraction result
4. Optionally persist or export the result

---

## Extraction requests

**Coming soon** — how to phrase requests, field names, and schemas.

---

## Understanding results

**Coming soon** — result shape, confidence, validation status, and error cases.

---

## Configuration

**Coming soon** — environment variables, model settings, storage paths (no secrets in this file; use env vars / secret managers).

---

## Troubleshooting

**Coming soon** — common errors and how to resolve them.

---

## Related docs

- [README.md](README.md) — project overview and layout
- [Development plan](Document-Reader-AI--Development-plan.md) — architecture and roadmap
