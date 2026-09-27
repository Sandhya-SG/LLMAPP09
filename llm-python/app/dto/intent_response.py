from pydantic import BaseModel, Field


class IntentResponse(BaseModel):
    """Intent detection result with primary and secondary intents."""

    primaryIntent: str = Field(
        ...,
        description="Primary intent detected",
        json_schema_extra={"example": "find_restaurant"},
    )
    secondaryIntents: list[str] = Field(
        ...,
        description="Secondary intents detected",
        json_schema_extra={"example": ["location_search", "recommendation_request"]},
    )
    intentCategory: str = Field(
        ...,
        description="Category of the intent",
        json_schema_extra={"example": "question"},
    )
    confidence: float = Field(
        ...,
        description="Confidence score (0.0 to 1.0)",
        json_schema_extra={"example": 0.88},
    )
