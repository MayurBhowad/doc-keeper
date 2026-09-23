# Document Reader AI (doc-keeper)

A small, developer-focused document reader and AI extraction engine.

Read a document → understand what was requested → extract fields → validate → store the result.

```text
invoice.pdf + "invoice number, vendor name, total"
  → { "invoice_number": "...", "vendor_name": "...", "total": ... }
```

> Documentation will expand as the project grows. See the [development plan](Document-Reader-AI--Development-plan.md) for architecture and phases.

---

## Status

**Early scaffolding** — core engine not implemented yet.

| Area | Status |
|------|--------|
| Core extraction engine | Planned |
| PDF / text readers | Planned |
| AI extraction | Planned |
| Validation | Planned |
| API | Planned |
| Production infra | Deferred |

---

## Quick start

*To be filled when install and run paths exist.*

```bash
# 1. Activate your pyenv environment (ask the maintainer for the env name)
# pyenv activate <env>

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run (command TBD)
```

---

## Project layout

```text
doc-keeper/
├── src/                 # Application source
├── tests/               # Tests
├── requirements.txt     # Python dependencies
├── README.md            # This file
├── user_guide.md        # How to use the product
└── Document-Reader-AI--Development-plan.md
```

---

## Documentation

| Doc | Purpose |
|-----|---------|
| [user_guide.md](user_guide.md) | End-user / operator usage |
| [Development plan](Document-Reader-AI--Development-plan.md) | Architecture, phases, component design |

---

## Development principles

- Small, modular, testable
- Local-first during development
- Core extraction engine first; infrastructure later
- Avoid premature microservices, queues, K8s, RAG, etc.

---

## Contributing

*Guidelines to be added as the codebase matures.*

---

## License

*TBD*
