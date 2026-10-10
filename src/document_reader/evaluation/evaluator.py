from dataclasses import dataclass
from typing import Any, Sequence

from document_reader.domain.content import DocumentContent
from document_reader.domain.extraction import (
    ExtractionRequest,
    ExtractionResult,
)
from document_reader.extractors.base import DocumentExtractor


@dataclass(frozen=True)
class FieldMismatch:
    field: str
    expected: Any
    actual: Any
    reason: str


@dataclass(frozen=True)
class EvaluationResult:
    passed: bool
    mismatches: list[FieldMismatch]


@dataclass(frozen=True)
class EvaluationCase:
    name: str
    content: DocumentContent
    request: ExtractionRequest
    expected: dict[str, Any]


@dataclass(frozen=True)
class EvaluationCaseResult:
    name: str
    passed: bool
    mismatches: list[FieldMismatch]


@dataclass(frozen=True)
class EvaluationSummary:
    total_cases: int
    passed_cases: int
    failed_cases: int
    results: list[EvaluationCaseResult]


class ExtractionEvaluator:
    def compare(
        self,
        expected: dict[str, Any],
        actual: dict[str, Any],
    ) -> EvaluationResult:
        mismatches = []

        for field, expected_value in expected.items():
            if field not in actual:
                mismatches.append(
                    FieldMismatch(
                        field=field,
                        expected=expected_value,
                        actual=None,
                        reason="missing",
                    )
                )
            elif actual[field] != expected_value:
                mismatches.append(
                    FieldMismatch(
                        field=field,
                        expected=expected_value,
                        actual=actual[field],
                        reason="incorrect",
                    )
                )

        for field, actual_value in actual.items():
            if field not in expected:
                mismatches.append(
                    FieldMismatch(
                        field=field,
                        expected=None,
                        actual=actual_value,
                        reason="unexpected",
                    )
                )

        return EvaluationResult(
            passed=not mismatches,
            mismatches=mismatches,
        )

    def evaluate(
        self,
        cases: Sequence[EvaluationCase],
        extractor: DocumentExtractor,
    ) -> EvaluationSummary:
        results = []

        for case in cases:
            extraction: ExtractionResult = extractor.extract(
                case.content,
                case.request,
            )

            comparison = self.compare(
                expected=case.expected,
                actual=extraction.data,
            )

            results.append(
                EvaluationCaseResult(
                    name=case.name,
                    passed=comparison.passed,
                    mismatches=comparison.mismatches,
                )
            )

        passed_cases = sum(result.passed for result in results)
        total_cases = len(results)

        return EvaluationSummary(
            total_cases=total_cases,
            passed_cases=passed_cases,
            failed_cases=total_cases - passed_cases,
            results=results,
        )