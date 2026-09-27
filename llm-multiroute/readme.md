# Project Structure                                                       
                                                                         
 llm-multiroute/                                                          │
 ├── app/                                                                 │
 │   ├── __init__.py                                                      │
 │   ├── main.py                        # FastAPI app entry point         │
 │   ├── config.py                      # Settings with per-route model config                                                                   │
 │   ├── router/                                                          │
 │   │   ├── __init__.py                                                  │
 │   │   └── model_router.py            # Maps task type → model name     │
 │   ├── controller/                                                      │
 │   │   ├── __init__.py                                                  │
 │   │   └── ai_controller.py           # 4 REST endpoints + GET /routes  │
 info                                                                     │
 │   ├── service/                                                         │
 │   │   ├── __init__.py                                                  │
 │   │   └── ai_service.py              # Ollama cloud API calls          │
 (model-aware)                                                            │
 │   └── dto/                                                             │
 │       ├── __init__.py                                                   │       ├── text_request.py                                              │
 │       ├── classification_response.py                                   │
 │       ├── sentiment_response.py                                        │
 │       ├── summary_response.py                                          │
 │       └── intent_response.py                                           │
 ├── tests/                                                               │
 │   ├── __init__.py                                                      │
 │   ├── test_ai_controller.py                                            │
 │   ├── test_ai_service.py                                               │
 │   └── test_model_router.py                                             │
 ├── requirements.txt                                                     │
 └── .env.example                                                         │
                                                                          │
#  Files to Create (17 files)
                                                                          
│ 1. requirements.txt                                                     
│                                                                          
│ - fastapi, uvicorn, httpx, pydantic, python-dotenv, pytest,              │
│ pytest-asyncio                                                           │
│                                                                          │
│ 2. app/config.py — Per-Route Model Configuration                         │
│                                                                          │
│ Environment variables:                                                   │
│ OLLAMA_BASE_URL       = https://api.ollama.com  (Ollama cloud)           │
│ OLLAMA_API_KEY        = (from env)                                       │
│ OLLAMA_TEMPERATURE    = 0.7                                              │
│                                                                          │
│ # Per-route model assignments (the core multi-route feature)             │
│ OLLAMA_MODEL_CLASSIFY  = gemma3:4b                                       │
│ OLLAMA_MODEL_SENTIMENT = llama3.2                                        │
│ OLLAMA_MODEL_SUMMARIZE = mistral                                         │
│ OLLAMA_MODEL_INTENT    = qwen2.5                                         │
│                                                                          │
│ 3. app/router/model_router.py — Task-to-Model Router                     │
│                                                                          │
│ - Defines TaskType enum: CLASSIFY, SENTIMENT, SUMMARIZE, INTENT          │
│ - ModelRouter class with get_model(task_type) -> str method              │
│ - get_routes() -> dict to expose the current routing table               │
│ - Reads model assignments from config.py                                 │
│                                                                          │
│ 4. app/service/ai_service.py — Model-Aware Ollama Service                │
│                                                                          │
│ - _chat(prompt, model) method — accepts model as parameter (not          │
│ hardcoded)                                                               │
│ - Each task method asks ModelRouter for the correct model, then calls    │
│ _chat                                                                    │
│ - Uses Authorization: Bearer {OLLAMA_API_KEY} header                     │
│ - Calls POST {OLLAMA_BASE_URL}/api/chat with stream: false               │
│ - Same prompt templates and JSON parsing as existing llm-python          │
│                                                                          │
│ 5. app/controller/ai_controller.py — REST Endpoints                      │
│                                                                          │
│ POST /api/ai/classify    → ClassificationResponse  (uses                 │
│ OLLAMA_MODEL_CLASSIFY)                                                   │
│ POST /api/ai/sentiment   → SentimentResponse        (uses                │
│ OLLAMA_MODEL_SENTIMENT)                                                  │
│ POST /api/ai/summarize   → SummaryResponse           (uses               │
│ OLLAMA_MODEL_SUMMARIZE)                                                  │
│ POST /api/ai/intent      → IntentResponse            (uses               │
│ OLLAMA_MODEL_INTENT)                                                     │
│ GET  /api/ai/routes      → current routing table     (which model        │
│ handles which task)                                                      │
│                                                                          │
│ 6. DTOs — Same Pydantic models as llm-python                             │
│                                                                          │
│ - text_request.py, classification_response.py, sentiment_response.py,    │
│ summary_response.py, intent_response.py                                  │
│                                                                          │
│ 7. app/main.py — FastAPI App                                             │
│                                                                          │
│ - Title: "Multi-Route LLM API"                                           │
│ - Include router, Swagger at /swagger-ui.html                            │
│                                                                          │
│ 8. .env.example — Template for required env vars                         │
│                                                                          │
│ 9. Tests                                                                 │
│                                                                          │
│ - test_model_router.py — verify correct model returned per task type     │
│ - test_ai_service.py — mock httpx, verify correct model passed to Ollama │
│  API                                                                     │
│ - test_ai_controller.py — endpoint integration tests                     │
│                                                                          │
│ Verification                                                             │
│                                                                          │
│ cd llm-multiroute                                                        │
│ pip install -r requirements.txt                                          │
│ # Set env vars or create .env                                            │
│ export OLLAMA_API_KEY=your_key                                           │
│ python -m uvicorn app.main:app --port 8080 --reload                      │
│ # Open http://localhost:8082/swagger-ui.html                             │
│ # Test: GET /api/ai/routes — should show 4 model assignments             │
│ # Test: POST /api/ai/classify with {"text": "AI is transforming          │
│ healthcare"}       

---

# Guardrails (guardrails-ai)

`app/guardrails/` wraps the [guardrails-ai](https://github.com/guardrails-ai/guardrails)
`Guard`/`Validator` framework and is wired into every request in two places:

**Input guard** (`ai_controller._guarded_input`, runs before the LLM call):
custom `Validator`s (`app/guardrails/validators.py`) detect prompt injection,
harmful-content requests, secrets/API keys, and PII in `request.text`.
Every detection is logged to `metrics/safety_metrics.json`
(`GET /api/ai/metrics/safety`); secrets and PII are additionally redacted
before the (possibly third-party) Ollama model ever sees them. Blocking
(HTTP 400) instead of logging is opt-in per category via env vars — off by
default so the documented "requests still get processed" behavior in
`metrics_testing.md` is preserved:

```
GUARDRAILS_BLOCK_PROMPT_INJECTION=true
GUARDRAILS_BLOCK_HARMFUL_CONTENT=true
GUARDRAILS_BLOCK_SECRETS=true
```

**Output guard** (`ai_service`, replaces the old regex + `json.loads` parsing):
`GuardrailsEngine.validate_output()` uses `Guard.for_pydantic(output_class=...)`
per response DTO to validate the raw model response against its schema —
required fields, types, numeric ranges (`confidence`/`sentimentScore`), and
allowed enum values (`overallSentiment`, `intentCategory`) — with automatic
markdown-fence stripping. A response that fails validation raises the same
`RuntimeError("Failed to parse AI response as JSON: ...")` as before, so a
malformed *or* now also a semantically-invalid response (e.g. `confidence: 5.0`,
an invented sentiment category) is rejected instead of silently accepted.

`GET /api/ai/guardrails` reports which guards are active and whether each
blocks or just logs/redacts. See `tests/test_guardrails.py` for coverage.