import os


def _bool_env(name: str, default: str) -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")


class Settings:
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8080"))
    APP_NAME: str = os.getenv("APP_NAME", "llm-multiroute")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "https://ollama.com")
    OLLAMA_TEMPERATURE: float = float(os.getenv("OLLAMA_TEMPERATURE", "0.7"))
    OLLAMA_API_KEY: str = os.getenv("OLLAMA_API_KEY", "")
    # Per-attempt timeout for Ollama calls. Kept short so all retry attempts
    # (see AIService.max_attempts) finish before a 120s client timeout.
    OLLAMA_TIMEOUT: float = float(os.getenv("OLLAMA_TIMEOUT", "30"))

    # Per-route model assignments (must be available on Ollama cloud)
    OLLAMA_MODEL_CLASSIFY: str = os.getenv("OLLAMA_MODEL_CLASSIFY", "gemma4:31b")
    OLLAMA_MODEL_SENTIMENT: str = os.getenv("OLLAMA_MODEL_SENTIMENT", "gpt-oss:120b")
    OLLAMA_MODEL_SUMMARIZE: str = os.getenv("OLLAMA_MODEL_SUMMARIZE", "nemotron-3-super")
    OLLAMA_MODEL_INTENT: str = os.getenv("OLLAMA_MODEL_INTENT", "gpt-oss:20b")

    # Guardrails: which detections block the request (400) vs. log-only.
    # PII is always redacted rather than blocked. Off by default so the
    # documented "requests still get processed, events are logged" behavior
    # is preserved; flip these on per deployment as needed.
    GUARDRAILS_BLOCK_PROMPT_INJECTION: bool = _bool_env("GUARDRAILS_BLOCK_PROMPT_INJECTION", "false")
    GUARDRAILS_BLOCK_HARMFUL_CONTENT: bool = _bool_env("GUARDRAILS_BLOCK_HARMFUL_CONTENT", "false")
    GUARDRAILS_BLOCK_SECRETS: bool = _bool_env("GUARDRAILS_BLOCK_SECRETS", "false")


settings = Settings()
