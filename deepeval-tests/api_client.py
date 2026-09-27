"""
API client for the Spring AI Text Analysis API running on localhost:8080.
Provides helper functions to call each endpoint and return structured responses.
"""

import requests

BASE_URL = "http://localhost:8080/api/ai"
HEADERS = {"Content-Type": "application/json"}
TIMEOUT = 120  # LLM responses can be slow


def classify_text(text: str) -> dict:
    """POST /api/ai/classify - Classify text with labels and categories."""
    response = requests.post(
        f"{BASE_URL}/classify",
        json={"text": text},
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def analyze_sentiment(text: str) -> dict:
    """POST /api/ai/sentiment - Analyze text sentiment and emotions."""
    response = requests.post(
        f"{BASE_URL}/sentiment",
        json={"text": text},
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def summarize_text(text: str) -> dict:
    """POST /api/ai/summarize - Summarize text with key points."""
    response = requests.post(
        f"{BASE_URL}/summarize",
        json={"text": text},
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def detect_intent(text: str) -> dict:
    """POST /api/ai/intent - Detect intent behind text."""
    response = requests.post(
        f"{BASE_URL}/intent",
        json={"text": text},
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()
