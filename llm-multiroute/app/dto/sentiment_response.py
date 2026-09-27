from typing import Literal

from pydantic import BaseModel, Field


class SentimentResponse(BaseModel):
    """Sentiment analysis result with emotions and confidence."""

    overallSentiment: Literal["positive", "negative", "neutral", "mixed"] = Field(
        ...,
        description="Overall sentiment classification",
        json_schema_extra={"example": "positive"},
    )
    sentimentScore: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        description="Sentiment score from -1 (negative) to 1 (positive)",
        json_schema_extra={"example": 0.85},
    )
    emotions: list[str] = Field(
        ...,
        description="Detected emotions in the text",
        json_schema_extra={"example": ["joy", "excitement"]},
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0 to 1.0)",
        json_schema_extra={"example": 0.92},
    )
