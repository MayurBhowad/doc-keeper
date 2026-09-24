from document_reader.domain.extraction import ExtractionRequest, ExtractionResult


def test_extraction_request():
    request = ExtractionRequest(query="Give me invoice number and total")

    assert request.query == "Give me invoice number and total"


def test_extraction_result():
    result = ExtractionResult(data={"invoice_number": "1234567890", "total": 100.00})

    assert result.data["invoice_number"] == "1234567890"
    assert result.data["total"] == 100.00