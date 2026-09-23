from document_reader import storage
from document_reader.storage.json import JsonStorage


def test_engine_processes_text_document(tmp_path):
    input_file = tmp_path / "hello.txt"
    input_file.write_text("Hello Document AI!", encoding="utf-8")

    output_dir = tmp_path / "output"

    from document_reader.engine import DocumentEngine

    engine = DocumentEngine(storage=JsonStorage(output_dir))

    result = engine.process(str(input_file))

    assert result["filename"] == "hello.txt"
    assert result["content"] == "Hello Document AI!"

    output_file = output_dir / "hello.json"

    assert output_file.exists()


def test_engine_processes_pdf_document(tmp_path):
    import fitz
    input_file = tmp_path / "hello.pdf"

    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "Hello PDF!")
    pdf.save(input_file)
    pdf.close()

    output_dir = tmp_path / "output"

    from document_reader.engine import DocumentEngine

    engine = DocumentEngine(storage=JsonStorage(output_dir))

    result = engine.process(str(input_file))

    assert result["filename"] == "hello.pdf"
    assert "Hello PDF!" in result["content"]

    output_file = output_dir / "hello.json"

    assert output_file.exists()


def test_engine_rejects_unsupported_document(tmp_path):
    input_file = tmp_path / "hello.docx"
    input_file.write_text("Hello Document AI!", encoding="utf-8")

    from document_reader.engine import DocumentEngine
    engine = DocumentEngine()

    try:
        engine.process(str(input_file))
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Unsupported document type" in str(exc)