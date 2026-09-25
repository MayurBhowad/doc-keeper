from document_reader.domain.content import DocumentContent
from document_reader.domain.extraction import ExtractionRequest
from document_reader.extractors.llm import LLMExtractor


class FakeLLMClient:

    def __init__(self):
        self.last_prompt = None

    def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        return {
            "invoice_number": "INV-123",
            "vendor_name": "ABC Pvt Ltd",
            "total": 15000,
        }

    
def test_llm_extractor():
    client = FakeLLMClient()

    extractor = LLMExtractor(client)

    content = DocumentContent(
        filename="invoice.pdf",
        document_type="pdf",
        text="Invoice INV-123 ABC Pvt Ltd Total 15000",
    )

    request = ExtractionRequest(
        query="Give me invoice number, vendor and total"
    )

    result = extractor.extract(content, request)

    assert result.data["invoice_number"] == "INV-123"
    assert result.data["vendor_name"] == "ABC Pvt Ltd"
    assert result.data["total"] == 15000