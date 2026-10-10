# Extraction Evaluation Guide

## Overview

Doc-Keeper provides a lightweight evaluation framework for comparing
extracted document data against expected results.

The evaluator is independent of any specific LLM provider. It accepts
a `DocumentExtractor`, allowing tests to use deterministic fake
extractors without external API calls.

## Comparison behavior

`ExtractionEvaluator.compare()` compares expected and actual dictionaries.

A comparison passes when both dictionaries contain the same fields
with equal values.

A failed comparison reports field-level mismatches:

- `missing`: an expected field is absent from the actual result.
- `unexpected`: an actual field is not present in the expected result.
- `incorrect`: a field exists in both dictionaries but its values differ.

Value comparison uses Python equality. It does not perform semantic
matching or automatically convert types.

## Evaluating multiple cases

An `EvaluationCase` contains:

- `name`: a descriptive case identifier.
- `content`: the `DocumentContent` to evaluate.
- `request`: the `ExtractionRequest`, including an optional schema.
- `expected`: the expected extracted dictionary.

Pass a collection of cases and a `DocumentExtractor` to
`ExtractionEvaluator.evaluate()`.

The returned `EvaluationSummary` includes the total, passed, and failed
case counts, plus an individual result for each case.

## Example

```python
from document_reader.domain.content import DocumentContent
from document_reader.domain.extraction import (
    ExtractionRequest,
    ExtractionResult,
)
from document_reader.evaluation import (
    EvaluationCase,
    ExtractionEvaluator,
)


class FakeExtractor:
    def extract(self, content, request):
        return ExtractionResult(
            data={"invoice_number": "INV-123", "total": 15000}
        )


case = EvaluationCase(
    name="invoice-example",
    content=DocumentContent(
        filename="invoice.txt",
        document_type="text",
        text="Invoice INV-123 Total 15000",
    ),
    request=ExtractionRequest(query="Extract invoice details"),
    expected={"invoice_number": "INV-123", "total": 15000},
)

summary = ExtractionEvaluator().evaluate([case], FakeExtractor())

assert summary.total_cases == 1
assert summary.passed_cases == 1
assert summary.failed_cases == 0