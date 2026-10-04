from pydantic import BaseModel


class ExtractionSchema(BaseModel):
    """Base class for structured document extraction schemas."""

    model_config = {
        "extra": "forbid",
    }