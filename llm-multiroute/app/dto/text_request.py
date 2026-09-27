from pydantic import BaseModel, Field


class TextRequest(BaseModel):
    """Request body containing text to analyze."""

    text: str = Field(
        ...,
        description="Text to be analyzed",
        json_schema_extra={"example": "I love this product! The quality is outstanding."},
    )
