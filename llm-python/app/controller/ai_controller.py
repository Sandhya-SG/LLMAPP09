from fastapi import APIRouter

from app.dto.classification_response import ClassificationResponse
from app.dto.intent_response import IntentResponse
from app.dto.sentiment_response import SentimentResponse
from app.dto.summary_response import SummaryResponse
from app.dto.text_request import TextRequest
from app.service.ai_service import AIService

router = APIRouter(prefix="/api/ai", tags=["AI Text Analysis"])

ai_service = AIService()


@router.post(
    "/classify",
    response_model=ClassificationResponse,
    summary="Classify Text",
    description="Analyzes text and returns classification labels, tags, and primary category",
)
def classify_text(request: TextRequest) -> ClassificationResponse:
    return ai_service.classify_text(request.text)


@router.post(
    "/sentiment",
    response_model=SentimentResponse,
    summary="Analyze Sentiment",
    description="Analyzes text sentiment (positive, negative, neutral) and detects specific emotions",
)
def analyze_sentiment(request: TextRequest) -> SentimentResponse:
    return ai_service.analyze_sentiment(request.text)


@router.post(
    "/summarize",
    response_model=SummaryResponse,
    summary="Summarize Text",
    description="Generates a concise summary with key points from the provided text",
)
def summarize_text(request: TextRequest) -> SummaryResponse:
    return ai_service.summarize_text(request.text)


@router.post(
    "/intent",
    response_model=IntentResponse,
    summary="Detect Intent",
    description="Identifies the intent and purpose behind the text (question, request, statement, command)",
)
def detect_intent(request: TextRequest) -> IntentResponse:
    return ai_service.detect_intent(request.text)
