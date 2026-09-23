from pathlib import Path
from document_reader.domain.content import DocumentContent
from document_reader.domain.document import Document


def test_document():
    document = Document(path=Path("documents/invoice.pdf"))

    assert document.filename == "invoice.pdf"
    assert document.extension == ".pdf"


def test_document_content():
    content = DocumentContent(filename="invoice.pdf", document_type="pdf", text="Invoice content")

    assert content.filename == "invoice.pdf"
    assert content.document_type == "pdf"
    assert content.text == "Invoice content"