import pytest
import math

from document_reader.domain.extraction import FieldMetadata


def test_field_metadata_accepts_confidence_and_source_pages():
    metadata = FieldMetadata(
        confidence=0.91,
        source_pages=(1, 3),
    )

    assert metadata.confidence == 0.91
    assert metadata.source_pages == (1, 3)


def test_field_metadata_allows_unknown_evidence():
    metadata = FieldMetadata()

    assert metadata.confidence is None
    assert metadata.source_pages == ()


@pytest.mark.parametrize("confidence", [-0.01, 1.01])
def test_field_metadata_rejects_out_of_range_confidence(confidence):
    with pytest.raises(ValueError, match="confidence"):
        FieldMetadata(confidence=confidence)


@pytest.mark.parametrize("page", [0, -1])
def test_field_metadata_rejects_invalid_source_pages(page):
    with pytest.raises(ValueError, match="source_pages"):
        FieldMetadata(source_pages=(page,))


def test_field_metadata_detects_low_confidence():
    assert FieldMetadata(confidence=0.49).is_low_confidence(threshold=0.5)
    assert not FieldMetadata(confidence=0.5).is_low_confidence(threshold=0.5)


def test_unknown_confidence_is_not_falsely_flagged():
    assert not FieldMetadata().is_low_confidence(threshold=0.5)


def test_field_metadata_rejects_invalid_threshold():
    with pytest.raises(ValueError, match="threshold"):
        FieldMetadata(confidence=0.8).is_low_confidence(threshold=1.1)


def test_extraction_result_accepts_field_metadata():
    from document_reader.domain.extraction import ExtractionResult

    result = ExtractionResult(
        data={"total": 15000},
        field_metadata={
            "total": FieldMetadata(
                confidence=0.91,
                source_pages=(2,),
            )
        },
    )

    assert result.data == {"total": 15000}
    assert result.field_metadata["total"].confidence == 0.91
    assert result.field_metadata["total"].source_pages == (2,)


def test_extraction_result_remains_backward_compatible():
    from document_reader.domain.extraction import ExtractionResult

    result = ExtractionResult(data={"total": 15000})

    assert result.data == {"total": 15000}
    assert result.metadata is None
    assert result.field_metadata == {}

@pytest.mark.parametrize("confidence", [math.nan, math.inf, -math.inf, True])
def test_field_metadata_rejects_non_finite_or_invalid_confidence(confidence):
    with pytest.raises(ValueError, match="confidence"):
        FieldMetadata(confidence=confidence)


@pytest.mark.parametrize("page", [True, 1.5, "2"])
def test_field_metadata_rejects_non_integer_source_pages(page):
    with pytest.raises(ValueError, match="source_pages"):
        FieldMetadata(source_pages=(page,))
