import fitz
from document_reader import storage
from document_reader.engine import DocumentEngine
from document_reader.extractors.llm import LLMExtractor
from document_reader.storage.json import JsonStorage
from document_reader.extractors.fake import FakeExtractor


class FakeLLMClient:

    def generate(self, prompt: str) -> str:
        return {
            "invoice_number": "INV-123",
            "vendor_name": "ABC Pvt Ltd",
            "total": 15000,
        }

def test_engine_processes_text_document(tmp_path):
    input_file = tmp_path / "hello.txt"
    input_file.write_text("Hello Document AI!", encoding="utf-8")

    output_dir = tmp_path / "output"

    from document_reader.engine import DocumentEngine

    engine = DocumentEngine(storage=JsonStorage(output_dir))

    result = engine.process(str(input_file), "Extract the document text")

    assert result["filename"] == "hello.txt"
    assert result["data"]["query"] == "Extract the document text"
    assert result["data"]["filename"] == "hello.txt"
    assert result["data"]["text"] == "Hello Document AI!"

    output_file = output_dir / "hello.json"

    assert output_file.exists()


def test_engine_processes_pdf_document(tmp_path):
    input_file = tmp_path / "hello.pdf"

    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "Hello PDF!")
    pdf.save(input_file)
    pdf.close()

    output_dir = tmp_path / "output"

    engine = DocumentEngine(storage=JsonStorage(output_dir))

    result = engine.process(str(input_file), "Extract the document text")

    assert result["filename"] == "hello.pdf"
    assert result["data"]["filename"] == "hello.pdf"
    assert "Hello PDF!" in result["data"]["text"]

    output_file = output_dir / "hello.json"

    assert output_file.exists()


def test_engine_rejects_unsupported_document(tmp_path):
    input_file = tmp_path / "hello.docx"
    input_file.write_text("Hello Document AI!", encoding="utf-8")

    engine = DocumentEngine(extractor=FakeExtractor())

    try:
        engine.process(str(input_file), "Extract the document text")
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Unsupported document type" in str(exc)


def test_engine_with_llm_extractor(tmp_path):
    input_file = tmp_path / "invoice.txt"

    input_file.write_text(
        "Invoice INV-123 ABC Pvt Ltd Total 15000",
        encoding="utf-8",
    )

    output_dir = tmp_path / "output"

    extractor = LLMExtractor(
        FakeLLMClient()
    )

    engine = DocumentEngine(
        extractor=extractor,
        storage=JsonStorage(output_dir),
    )

    result = engine.process(
        str(input_file),
        "Give me invoice number, vendor and total",
    )

    assert result["filename"] == "invoice.txt"
    assert result["data"]["invoice_number"] == "INV-123"
    assert result["data"]["vendor_name"] == "ABC Pvt Ltd"
    assert result["data"]["total"] == 15000

    assert (output_dir / "invoice.json").exists()