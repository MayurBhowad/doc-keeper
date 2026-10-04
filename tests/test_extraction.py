from document_reader.domain.extraction import ExtractionRequest, ExtractionResult
from document_reader.domain.schema import ExtractionSchema

class InvoiceExtraction(ExtractionSchema):
    invoice_number: str
    vendor_name: str
    total: float


def test_extraction_request():
    request = ExtractionRequest(query="Give me invoice number and total")

    assert request.query == "Give me invoice number and total"


def test_extraction_result():
    result = ExtractionResult(data={"invoice_number": "1234567890", "total": 100.00})

    assert result.data["invoice_number"] == "1234567890"
    assert result.data["total"] == 100.00


def test_extraction_request_with_schema():
    request = ExtractionRequest(
        query="Extract invoice details",
        schema=InvoiceExtraction,
    )

    assert request.query == "Extract invoice details"
    assert request.schema is InvoiceExtraction
