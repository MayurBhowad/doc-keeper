from document_reader.domain.extraction import ExtractionRequest, ExtractionResult


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
        schema={
            "invoice_number": "string",
            "vendor_name": "string",
            "total": "number",
        },
    )

    assert request.query == "Extract invoice details"
    assert request.schema["invoice_number"] == "string"
    assert request.schema["vendor_name"] == "string"
    assert request.schema["total"] == "number"
