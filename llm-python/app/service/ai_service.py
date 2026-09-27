import json
import re
from typing import Optional

import httpx

from app.config import settings
from app.dto.classification_response import ClassificationResponse
from app.dto.intent_response import IntentResponse
from app.dto.sentiment_response import SentimentResponse
from app.dto.summary_response import SummaryResponse


class AIService:
    def __init__(self, http_client: Optional[httpx.Client] = None):
        self.http_client = http_client or httpx.Client(timeout=120.0)
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.temperature = settings.OLLAMA_TEMPERATURE
        self.api_key = settings.OLLAMA_API_KEY

    def _chat(self, prompt: str) -> str:
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        response = self.http_client.post(
            f"{self.base_url}/api/chat",
            headers=headers,
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {"temperature": self.temperature},
            },
        )
        response.raise_for_status()
        return response.json()["message"]["content"]

    def classify_text(self, text: str) -> ClassificationResponse:
        prompt = (
            "Analyze the following text and classify it with appropriate labels and tags. "
            "Respond with ONLY valid JSON, no additional text or explanation.\n\n"
            f"Text: {text}\n\n"
            "Return JSON in this exact format:\n"
            '{"labels": ["label1", "label2"], "primaryCategory": "category", "confidence": 0.9}'
        )
        response = self._chat(prompt)
        return self._parse_json(response, ClassificationResponse)

    def analyze_sentiment(self, text: str) -> SentimentResponse:
        prompt = (
            "Analyze the sentiment of the following text. "
            "Respond with ONLY valid JSON, no additional text or explanation.\n\n"
            f"Text: {text}\n\n"
            "Return JSON in this exact format:\n"
            '{"overallSentiment": "positive", "sentimentScore": 0.8, '
            '"emotions": ["joy", "excitement"], "confidence": 0.9}'
        )
        response = self._chat(prompt)
        return self._parse_json(response, SentimentResponse)

    def summarize_text(self, text: str) -> SummaryResponse:
        prompt = (
            "Summarize the following text concisely. "
            "Respond with ONLY valid JSON, no additional text or explanation.\n\n"
            f"Text: {text}\n\n"
            "Return JSON in this exact format:\n"
            '{"summary": "your summary here", "keyPoints": ["point1", "point2", "point3"], "wordCount": 25}'
        )
        response = self._chat(prompt)
        return self._parse_json(response, SummaryResponse)

    def detect_intent(self, text: str) -> IntentResponse:
        prompt = (
            "Detect the intent behind the following text. "
            "Respond with ONLY valid JSON, no additional text or explanation.\n\n"
            f"Text: {text}\n\n"
            "Return JSON in this exact format:\n"
            '{"primaryIntent": "main_intent", "secondaryIntents": ["intent1", "intent2"], '
            '"intentCategory": "question", "confidence": 0.9}'
        )
        response = self._chat(prompt)
        return self._parse_json(response, IntentResponse)

    @staticmethod
    def _parse_json(raw: str, model_class: type):
        cleaned = raw.strip()
        # Strip markdown code blocks if present
        cleaned = re.sub(r"^```json\s*", "", cleaned)
        cleaned = re.sub(r"^```\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()
        try:
            data = json.loads(cleaned)
            return model_class(**data)
        except Exception as e:
            raise RuntimeError(f"Failed to parse AI response as JSON: {raw}") from e
