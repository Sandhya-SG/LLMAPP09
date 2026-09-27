# Project Structure

  llm-python/
  ├── requirements.txt              # FastAPI, uvicorn, httpx, pydantic,
  pytest
  ├── app/
  │   ├── __init__.py
  │   ├── main.py                   # FastAPI app entry point (Swagger at
  /swagger-ui.html)
  │   ├── config.py                 # Settings (Ollama URL, model,
  temperature)
  │   ├── controller/
  │   │   ├── __init__.py
  │   │   └── ai_controller.py     # 4 REST endpoints under /api/ai/
  │   ├── service/
  │   │   ├── __init__.py
  │   │   └── ai_service.py        # Ollama chat integration + JSON parsing 
  │   └── dto/
  │       ├── __init__.py
  │       ├── text_request.py       # Pydantic request model
  │       ├── classification_response.py
  │       ├── sentiment_response.py
  │       ├── summary_response.py
  │       └── intent_response.py tests/
      ├── __init__.py 
      ├── test_ai_controller.py     # 19 endpoint tests
      └── test_ai_service.py        # 22 service/parsing tests

  # Mapping Summary
  ┌───────────────────────────────┬─────────────────────────────────────┐
  │          Spring Boot          │          Python (FastAPI)           │
  ├───────────────────────────────┼─────────────────────────────────────┤  
  │ Spring Boot Web               │ FastAPI + Uvicorn                   │
  ├───────────────────────────────┼─────────────────────────────────────┤  
  │ Spring AI ChatClient (Ollama) │ httpx (direct Ollama REST API)      │
  ├───────────────────────────────┼─────────────────────────────────────┤
  │ Java DTOs with Jackson        │ Pydantic models                     │
  ├───────────────────────────────┼─────────────────────────────────────┤
  │ SpringDoc OpenAPI / Swagger   │ FastAPI built-in OpenAPI            │
  ├───────────────────────────────┼─────────────────────────────────────┤
  │ JUnit 5 + Mockito             │ pytest + unittest.mock              │
  ├───────────────────────────────┼─────────────────────────────────────┤
  │ application.yml               │ Environment variables via config.py │
  └───────────────────────────────┴─────────────────────────────────────┘
  
  # Endpoints (identical to Spring Boot)
  - POST /api/ai/classify - Text classification
  - POST /api/ai/sentiment - Sentiment analysis
  - POST /api/ai/summarize - Text summarization
  - POST /api/ai/intent - Intent detection
  
  # Running
  cd llm-python
  pip install -r requirements.txt
  python3 -m uvicorn app.main:app --port 8080 --reload

  Swagger UI is at http://localhost:8080/swagger-ui.html (same Ollama
  requirement: http://localhost:11434 with gemma:2b).

  # Files modified

  app/config.py - Added OLLAMA_API_KEY setting and changed default base URL:
  - OLLAMA_BASE_URL default changed from http://localhost:11434 to
  https://ollama.com
  - Added OLLAMA_API_KEY: str = os.getenv("OLLAMA_API_KEY", "")
  app/service/ai_service.py - Added Bearer token authentication to API
  requests:
  - Reads api_key from settings.OLLAMA_API_KEY
  - When api_key is set, adds Authorization: Bearer <key> header to all HTTP requests to the Ollama cloud API
  - When no key is configured, no auth header is sent (backward compatible with local instances)
  tests/test_ai_service.py - Added 2 new tests for auth header behavior:
  - test_api_key_sends_bearer_header - verifies the Authorization: Bearer
  header is included when an API key is configured
  - test_no_api_key_sends_no_auth_header - verifies no auth header is sent when the API key is empty

  # Usage
  Set the OLLAMA_API_KEY environment variable with your Ollama cloud API
  key:
  export OLLAMA_API_KEY="your-api-key-here"

  The application will then authenticate against https://ollama.com/api chat using Authorization: Bearer $OLLAMA_API_KEY. You can still override
  OLLAMA_BASE_URL if needed for a different Ollama instance.


  # Summary of all changes

  app/config.py — 2 changes:
  - Default OLLAMA_BASE_URL changed from http://localhost:11434 to
  https://ollama.com
  - Default OLLAMA_MODEL changed from gemma:2b to gemma3:4b (cloud-availablemodel)
  - Added OLLAMA_API_KEY setting read from environment
  app/service/ai_service.py — Added Bearer auth header:
  - Reads api_key from settings
  - Sends Authorization: Bearer <key> header on all requests when the key is set
  tests/test_ai_service.py — 2 new tests for auth header behavior

  You can override the model via OLLAMA_MODEL env var. Available cloud
  models include gemma3:4b, gemma3:12b, gemma3:27b, deepseek-v3.2,
  qwen3-coder:480b, gpt-oss:120b, and others — the full list is at
  https://ollama.com/search?c=cloud.
  
  Sources:
  - https://docs.ollama.com/cloud
  - https://docs.ollama.com/api/authentication