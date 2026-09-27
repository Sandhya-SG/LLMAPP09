from pydantic import BaseModel, Field


class SummaryResponse(BaseModel):
    """Text summarization result with key points."""

    summary: str = Field(
        ...,
        description="Concise summary of the text",
        json_schema_extra={"example": "This article discusses the impact of AI on healthcare..."},
    )
    keyPoints: list[str] = Field(
        ...,
        description="Key points extracted from the text",
        json_schema_extra={"example": ["AI improves diagnosis", "Reduces costs", "Enhances patient care"]},
    )
    wordCount: int = Field(
        ...,
        description="Word count of the summary",
        json_schema_extra={"example": 50},
    )
