from pydantic import BaseModel, Field


class ClassificationResponse(BaseModel):
    """Text classification result with labels and confidence."""

    labels: list[str] = Field(
        ...,
        description="List of classification labels/tags",
        json_schema_extra={"example": ["technology", "news", "AI"]},
    )
    primaryCategory: str = Field(
        ...,
        description="Primary category of the text",
        json_schema_extra={"example": "technology"},
    )
    confidence: float = Field(
        ...,
        description="Confidence score (0.0 to 1.0)",
        json_schema_extra={"example": 0.95},
    )
