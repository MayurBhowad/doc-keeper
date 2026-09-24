from document_reader.domain.content import DocumentContent
from document_reader.domain.extraction import ExtractionRequest
from document_reader.extractors.fake import FakeExtractor


def test_fake_extractor():
    content = DocumentContent(filename="invoice.txt", document_type="text", text="Invoice INV-001 Total 1500")
    request = ExtractionRequest(query="Give me invoice number and total")
    result = FakeExtractor().extract(content, request)

    assert result.data["query"] == "Give me invoice number and total"
    assert result.data["filename"] == "invoice.txt"
    assert result.data["text"] == "Invoice INV-001 Total 1500"