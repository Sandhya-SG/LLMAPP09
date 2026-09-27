from fastapi import APIRouter, HTTPException

from app.config import settings
from app.dto.classification_response import ClassificationResponse
from app.dto.intent_response import IntentResponse
from app.dto.sentiment_response import SentimentResponse
from app.dto.summary_response import SummaryResponse
from app.dto.text_request import TextRequest
from app.guardrails import GuardrailBlockedError, guardrails_engine
from app.monitoring import metrics_store
from app.router.model_router import model_router
from app.service.ai_service import AIService

router = APIRouter(prefix="/api/ai", tags=["AI Text Analysis"])

ai_service = AIService()


def _guarded_input(text: str, task_type: str) -> str:
    """Runs the input guardrails and returns the (possibly redacted) text to
    send to the model, or raises HTTPException if a detection blocks it."""
    try:
        return guardrails_engine.check_input(text, task_type)
    except GuardrailBlockedError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Request blocked by guardrail [{e.category}]: {e.details}",
        )


@router.post(
    "/classify",
    response_model=ClassificationResponse,
    summary="Classify Text",
    description="Analyzes text and returns classification labels, tags, and primary category",
)
def classify_text(request: TextRequest) -> ClassificationResponse:
    text = _guarded_input(request.text, "classify")
    return ai_service.classify_text(text)


@router.post(
    "/sentiment",
    response_model=SentimentResponse,
    summary="Analyze Sentiment",
    description="Analyzes text sentiment (positive, negative, neutral) and detects specific emotions",
)
def analyze_sentiment(request: TextRequest) -> SentimentResponse:
    text = _guarded_input(request.text, "sentiment")
    return ai_service.analyze_sentiment(text)


@router.post(
    "/summarize",
    response_model=SummaryResponse,
    summary="Summarize Text",
    description="Generates a concise summary with key points from the provided text",
)
def summarize_text(request: TextRequest) -> SummaryResponse:
    text = _guarded_input(request.text, "summarize")
    return ai_service.summarize_text(text)


@router.post(
    "/intent",
    response_model=IntentResponse,
    summary="Detect Intent",
    description="Identifies the intent and purpose behind the text (question, request, statement, command)",
)
def detect_intent(request: TextRequest) -> IntentResponse:
    text = _guarded_input(request.text, "intent")
    return ai_service.detect_intent(text)


@router.get(
    "/routes",
    summary="Get Route Configuration",
    description="Returns the current model routing table showing which model handles each task type",
)
def get_routes() -> dict[str, str]:
    return model_router.get_routes()


@router.get(
    "/guardrails",
    summary="Get Guardrails Configuration",
    description="Returns the active input/output guardrails and which detections block requests",
)
def get_guardrails_config() -> dict:
    return {
        "input_guards": {
            "prompt_injection_detector": {
                "action": "block" if settings.GUARDRAILS_BLOCK_PROMPT_INJECTION else "log_only",
            },
            "harmful_content_detector": {
                "action": "block" if settings.GUARDRAILS_BLOCK_HARMFUL_CONTENT else "log_only",
            },
            "secrets_present_detector": {
                "action": "block" if settings.GUARDRAILS_BLOCK_SECRETS else "redact",
            },
            "pii_detector": {"action": "redact"},
        },
        "output_guards": {
            "schema_validation": "Guard.for_pydantic per response DTO (type/range/enum checks)",
        },
    }


# ── Metrics endpoints ─────────────────────────────────────────────


@router.get(
    "/metrics/cost",
    summary="Get Cost Metrics",
    description="Returns token usage records and summary totals",
)
def get_cost_metrics() -> dict:
    return metrics_store.get_cost_metrics()


@router.get(
    "/metrics/performance",
    summary="Get Performance Metrics",
    description="Returns latency records with p50/p95/avg statistics",
)
def get_performance_metrics() -> dict:
    return metrics_store.get_performance_metrics()


@router.get(
    "/metrics/safety",
    summary="Get Safety Metrics",
    description="Returns prompt injection and policy violation records",
)
def get_safety_metrics() -> dict:
    return metrics_store.get_safety_metrics()
