import fitz

from document_reader.domain.document import Document
from document_reader.readers.pdf import PDFReader
from document_reader.readers.text import TextReader
from unittest.mock import patch

import pytest

from document_reader.readers.ocr import TesseractOCR


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


def test_pdf_reader_skips_ocr_when_text_is_available(tmp_path):
    file_path = tmp_path / "text.pdf"

    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "Readable PDF content")
    pdf.save(file_path)
    pdf.close()

    def unexpected_ocr(_page):
        raise AssertionError("OCR should not run for text-based PDFs")

    content = PDFReader(ocr=unexpected_ocr).read(
        Document(path=file_path)
    )

    assert "Readable PDF content" in content.text


def test_pdf_reader_uses_ocr_when_text_is_missing(tmp_path):
    file_path = tmp_path / "scanned.pdf"

    # An empty page simulates a PDF page with no extractable text.
    pdf = fitz.open()
    pdf.new_page()
    pdf.save(file_path)
    pdf.close()

    ocr_calls = []

    def fake_ocr(page):
        ocr_calls.append(page.number)
        return "Recognized scanned text"

    content = PDFReader(ocr=fake_ocr).read(
        Document(path=file_path)
    )

    assert ocr_calls == [0]
    assert content.text == "Recognized scanned text"


def test_pdf_reader_combines_ocr_text_in_page_order(tmp_path):
    file_path = tmp_path / "two_pages.pdf"

    pdf = fitz.open()
    pdf.new_page()
    pdf.new_page()
    pdf.save(file_path)
    pdf.close()

    def fake_ocr(page):
        return f"Recognized page {page.number + 1}"

    content = PDFReader(ocr=fake_ocr).read(
        Document(path=file_path)
    )

    assert content.text == "Recognized page 1\nRecognized page 2"


def test_tesseract_ocr_reports_missing_pytesseract():
    page = fitz.open().new_page()

    with patch(
        "document_reader.readers.ocr.importlib.util.find_spec",
        return_value=None,
    ):
        with pytest.raises(RuntimeError, match="pytesseract"):
            TesseractOCR()(page)

def test_tesseract_ocr_reports_missing_executable():
    page = fitz.open().new_page()

    with (
        patch(
            "document_reader.readers.ocr.importlib.util.find_spec",
            return_value=object(),
        ),
        patch(
            "document_reader.readers.ocr.shutil.which",
            return_value=None,
        ),
    ):
        with pytest.raises(RuntimeError, match="Tesseract executable"):
            TesseractOCR()(page)

def test_reader_registry_enables_ocr_for_pdfs():
    from document_reader.readers.ocr import TesseractOCR
    from document_reader.readers.registry import ReaderRegistry

    reader = ReaderRegistry().get(".pdf")

    assert isinstance(reader, PDFReader)
    assert isinstance(reader.ocr, TesseractOCR)


def test_pdf_reader_uses_configured_threshold(tmp_path):
    file_path = tmp_path / "short_text.pdf"

    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "Hi")
    pdf.save(file_path)
    pdf.close()

    content = PDFReader(
        ocr=lambda page: "OCR fallback text",
        min_text_chars=10,
    ).read(Document(path=file_path))

    assert content.text == "OCR fallback text"


def test_pdf_reader_rejects_invalid_threshold():
    import pytest

    with pytest.raises(ValueError, match="min_text_chars"):
        PDFReader(min_text_chars=0)


def test_tesseract_ocr_reports_missing_pillow():
    from unittest.mock import patch

    page = fitz.open().new_page()

    with (
        patch(
            "document_reader.readers.ocr.importlib.util.find_spec",
            side_effect=lambda name: None if name == "PIL" else object(),
        ),
        patch(
            "document_reader.readers.ocr.shutil.which",
            return_value="/usr/bin/tesseract",
        ),
    ):
        with pytest.raises(RuntimeError, match="Pillow"):
            TesseractOCR()(page)
