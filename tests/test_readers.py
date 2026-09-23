import fitz

from document_reader.domain.document import Document
from document_reader.readers.pdf import PDFReader
from document_reader.readers.text import TextReader


def test_text_reader(tmp_path):
    file_path = tmp_path / "hello.txt"

    file_path.write_text("Hello Document AI!", encoding="utf-8")

    document = Document(path=file_path)

    content = TextReader().read(document)

    assert content.filename == "hello.txt"
    assert content.document_type == "text"
    assert content.text == "Hello Document AI!"


def test_pdf_reader(tmp_path):
    file_path = tmp_path / "hello.pdf"

    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "Hello PDF!")
    pdf.save(file_path)
    pdf.close()

    document = Document(path=file_path)

    content = PDFReader().read(document)

    assert content.filename == "hello.pdf"
    assert content.document_type == "pdf"
    assert "Hello PDF!" in content.text