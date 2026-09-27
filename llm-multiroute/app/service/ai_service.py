import time

import httpx
from langfuse import get_client, observe

from app.config import settings
from app.dto.classification_response import ClassificationResponse
from app.dto.intent_response import IntentResponse
from app.dto.sentiment_response import SentimentResponse
from app.dto.summary_response import SummaryResponse
from app.guardrails import guardrails_engine
from app.monitoring import metrics_store
from app.router.model_router import ModelRouter, TaskType, model_router

langfuse = get_client()

# Upstream statuses worth retrying: rate limiting and transient server errors
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class AIService:
    max_attempts: int = 3
    retry_backoff: float = 1.0

    def __init__(
        self,
        http_client: httpx.Client | None = None,
        router: ModelRouter | None = None,
    ):
        self.http_client = http_client or httpx.Client(timeout=120.0)
        self.base_url = settings.OLLAMA_BASE_URL
        self.temperature = settings.OLLAMA_TEMPERATURE
        self.api_key = settings.OLLAMA_API_KEY
        self.router = router or model_router

    @observe(as_type="generation")
    def _chat(self, prompt: str, model: str, task_type: str = "unknown") -> str:
        langfuse.update_current_generation(
            name="ollama-chat",
            model=model,
            input=[{"role": "user", "content": prompt}],
            metadata={"temperature": self.temperature, "task_type": task_type},
        )

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        start = time.monotonic()
        response = self.http_client.post(
            f"{self.base_url}/api/chat",
            headers=headers,
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {"temperature": self.temperature},
            },
        )
        response.raise_for_status()
        latency = time.monotonic() - start

        body = response.json()
        input_tokens = body.get("prompt_eval_count", 0)
        output_tokens = body.get("eval_count", 0)
        content = body["message"]["content"]

        langfuse.update_current_generation(
            output=content,
            usage_details={"input": input_tokens, "output": output_tokens},
        )

        metrics_store.record_latency(task_type, model, latency)
        metrics_store.record_token_usage(
            task_type, model, input_tokens, output_tokens, input_tokens + output_tokens
        )

        return content

    def _chat_and_validate(self, prompt: str, model: str, task_type: str, model_class):
        """Calls the model and validates its output, retrying transient upstream
        errors (with backoff) and unparseable responses (immediately)."""
        for attempt in range(1, self.max_attempts + 1):
            try:
                response = self._chat(prompt, model, task_type=task_type)
                return guardrails_engine.validate_output(response, model_class, task_type=task_type)
            except httpx.HTTPStatusError as e:
                if e.response.status_code not in _RETRYABLE_STATUS or attempt == self.max_attempts:
                    raise
                time.sleep(self.retry_backoff * attempt)
            except httpx.TransportError:
                if attempt == self.max_attempts:
                    raise
                time.sleep(self.retry_backoff * attempt)
            except RuntimeError:
                if attempt == self.max_attempts:
                    raise

    def classify_text(self, text: str) -> ClassificationResponse:
        model = self.router.get_model(TaskType.CLASSIFY)
        prompt = (
            "Analyze the following text and classify it with appropriate labels and tags. "
            "Respond with ONLY valid JSON, no additional text or explanation.\n\n"
            f"Text: {text}\n\n"
            "Return JSON in this exact format:\n"
            '{"labels": ["label1", "label2"], "primaryCategory": "category", "confidence": 0.9}'
        )
        return self._chat_and_validate(prompt, model, "classify", ClassificationResponse)

    def analyze_sentiment(self, text: str) -> SentimentResponse:
        model = self.router.get_model(TaskType.SENTIMENT)
        prompt = (
            "Analyze the sentiment of the following text. "
            "Respond with ONLY valid JSON, no additional text or explanation.\n\n"
            f"Text: {text}\n\n"
            "sentimentScore must be a number from -1 to 1 that is numerically "
            "consistent with overallSentiment: strongly negative text should score "
            "close to -1, strongly positive text should score close to 1, neutral "
            "text should score close to 0, and mixed text (containing both clearly "
            "positive and clearly negative elements) should score close to 0, "
            "reflecting the balance between the positive and negative elements "
            "rather than only the negative ones. Do not default to positive scores "
            "for negative or neutral text, and do not default to negative scores "
            "for mixed text.\n\n"
            "emotions must include at least one emotion representing each distinct "
            "sentiment present in the text — for mixed text, include emotions for "
            "both the positive elements (e.g. admiration, satisfaction) and the "
            "negative elements (e.g. disappointment, frustration), not just one side.\n\n"
            "Examples:\n"
            'Negative text -> {"overallSentiment": "negative", "sentimentScore": -0.8, '
            '"emotions": ["anger", "disappointment"], "confidence": 0.9}\n'
            'Positive text -> {"overallSentiment": "positive", "sentimentScore": 0.8, '
            '"emotions": ["joy", "excitement"], "confidence": 0.9}\n'
            'Mixed text -> {"overallSentiment": "mixed", "sentimentScore": 0.1, '
            '"emotions": ["admiration", "disappointment"], "confidence": 0.9}\n\n'
            "Return JSON in this exact format:\n"
            '{"overallSentiment": "positive|negative|neutral|mixed", "sentimentScore": 0.0, '
            '"emotions": ["emotion1", "emotion2"], "confidence": 0.9}'
        )
        return self._chat_and_validate(prompt, model, "sentiment", SentimentResponse)

    def summarize_text(self, text: str) -> SummaryResponse:
        model = self.router.get_model(TaskType.SUMMARIZE)
        prompt = (
            "Summarize the following text concisely. "
            "Respond with ONLY valid JSON, no additional text or explanation.\n\n"
            f"Text: {text}\n\n"
            "Return JSON in this exact format:\n"
            '{"summary": "your summary here", "keyPoints": ["point1", "point2", "point3"], "wordCount": 25}'
        )
        return self._chat_and_validate(prompt, model, "summarize", SummaryResponse)

    def detect_intent(self, text: str) -> IntentResponse:
        model = self.router.get_model(TaskType.INTENT)
        prompt = (
            "Detect the intent behind the following text. "
            "Respond with ONLY valid JSON, no additional text or explanation.\n\n"
            f"Text: {text}\n\n"
            "intentCategory must be exactly one of:\n"
            "- question: the text asks for information\n"
            "- request: the text politely asks someone to do something\n"
            "- command: the text gives a direct order or instruction\n"
            "- statement: the text declares facts or information\n\n"
            "primaryIntent must be a short, specific phrase describing what the "
            "text is actually about or trying to accomplish (the topic/purpose), "
            "NOT a restatement of intentCategory. For example, for a command about "
            "smart home devices, primaryIntent should be something like 'home "
            "automation control', not 'command'.\n\n"
            "secondaryIntents must list other distinct purposes present in the "
            "text, if any. Do not repeat primaryIntent or intentCategory in this "
            "list; return an empty array if there are none.\n\n"
            "Example:\n"
            'Text: "Turn off the lights and lock the doors." -> '
            '{"primaryIntent": "home automation control", "secondaryIntents": [], '
            '"intentCategory": "command", "confidence": 0.9}\n\n'
            "Return JSON in this exact format:\n"
            '{"primaryIntent": "specific purpose description", "secondaryIntents": ["intent1"], '
            '"intentCategory": "question", "confidence": 0.9}'
        )
        return self._chat_and_validate(prompt, model, "intent", IntentResponse)
