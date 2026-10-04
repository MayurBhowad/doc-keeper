from pydantic import BaseModel, ConfigDict


class ExtractionSchema(BaseModel):
    """Base class for structured document extraction schemas."""

    model_config = ConfigDict(
        extra="forbid",
        strict=True,
    )
