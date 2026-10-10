from document_reader.domain.content import DocumentContent
from document_reader.domain.extraction import (
    ExtractionRequest,
    ExtractionResult,
)
from document_reader.evaluation.evaluator import (
    EvaluationCase,
    ExtractionEvaluator,
)


def test_evaluator_passes_when_extracted_data_matches_expected():
    evaluator = ExtractionEvaluator()

    result = evaluator.compare(
        expected={"invoice_number": "INV-123", "total": 15000},
        actual={"invoice_number": "INV-123", "total": 15000},
    )

    assert result.passed is True
    assert result.mismatches == []


def test_evaluator_reports_missing_fields():
    evaluator = ExtractionEvaluator()

    result = evaluator.compare(
        expected={"invoice_number": "INV-123", "total": 15000},
        actual={"invoice_number": "INV-123"},
    )

    assert result.passed is False
    assert len(result.mismatches) == 1
    assert result.mismatches[0].field == "total"
    assert result.mismatches[0].reason == "missing"


def test_evaluator_reports_unexpected_fields():
    evaluator = ExtractionEvaluator()

    result = evaluator.compare(
        expected={"invoice_number": "INV-123"},
        actual={"invoice_number": "INV-123", "currency": "INR"},
    )

    assert result.passed is False
    assert len(result.mismatches) == 1
    assert result.mismatches[0].field == "currency"
    assert result.mismatches[0].reason == "unexpected"


def test_evaluator_reports_incorrect_values():
    evaluator = ExtractionEvaluator()

    result = evaluator.compare(
        expected={"invoice_number": "INV-123", "total": 15000},
        actual={"invoice_number": "INV-123", "total": 12000},
    )

    assert result.passed is False
    assert len(result.mismatches) == 1
    assert result.mismatches[0].field == "total"
    assert result.mismatches[0].expected == 15000
    assert result.mismatches[0].actual == 12000
    assert result.mismatches[0].reason == "incorrect"


def test_evaluator_summarizes_multiple_cases():
    class FakeExtractor:
        def extract(self, content, request):
            if content.filename == "invoice-1.pdf":
                return ExtractionResult(
                    data={"invoice_number": "INV-001", "total": 1000}
                )

            return ExtractionResult(
                data={"invoice_number": "INV-002", "total": 2000}
            )

    cases = [
        EvaluationCase(
            name="correct-invoice",
            content=DocumentContent(
                filename="invoice-1.pdf",
                document_type="pdf",
                text="Invoice INV-001 Total 1000",
            ),
            request=ExtractionRequest(query="Extract invoice details"),
            expected={"invoice_number": "INV-001", "total": 1000},
        ),
        EvaluationCase(
            name="incorrect-invoice",
            content=DocumentContent(
                filename="invoice-2.pdf",
                document_type="pdf",
                text="Invoice INV-002 Total 2000",
            ),
            request=ExtractionRequest(query="Extract invoice details"),
            expected={"invoice_number": "INV-002", "total": 2500},
        ),
    ]

    summary = ExtractionEvaluator().evaluate(cases, FakeExtractor())

    assert summary.total_cases == 2
    assert summary.passed_cases == 1
    assert summary.failed_cases == 1
    assert summary.results[0].name == "correct-invoice"
    assert summary.results[0].passed is True
    assert summary.results[1].name == "incorrect-invoice"
    assert summary.results[1].passed is False
    assert summary.results[1].mismatches[0].field == "total"


def test_evaluator_returns_zero_counts_for_empty_cases():
    class NeverCalledExtractor:
        def extract(self, content, request):
            raise AssertionError("Extractor should not be called")

    summary = ExtractionEvaluator().evaluate(
        cases=[],
        extractor=NeverCalledExtractor(),
    )

    assert summary.total_cases == 0
    assert summary.passed_cases == 0
    assert summary.failed_cases == 0
    assert summary.results == []


def test_evaluator_passes_optional_schema_to_extractor():
    from document_reader.domain.schema import ExtractionSchema

    class InvoiceSchema(ExtractionSchema):
        invoice_number: str

    class InspectingExtractor:
        received_request = None

        def extract(self, content, request):
            self.received_request = request
            return ExtractionResult(
                data={"invoice_number": "INV-123"}
            )

    extractor = InspectingExtractor()
    schema = InvoiceSchema

    case = EvaluationCase(
        name="invoice-schema",
        content=DocumentContent(
            filename="invoice.pdf",
            document_type="pdf",
            text="Invoice INV-123",
        ),
        request=ExtractionRequest(
            query="Extract invoice number",
            schema=schema,
        ),
        expected={"invoice_number": "INV-123"},
    )

    summary = ExtractionEvaluator().evaluate([case], extractor)

    assert summary.passed_cases == 1
    assert extractor.received_request.schema is schema