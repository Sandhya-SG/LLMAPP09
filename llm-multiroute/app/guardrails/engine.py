"""Guardrails-ai wiring for llm-multiroute: input safety checks + structured
output validation, built on top of `guardrails.Guard`.
"""

from typing import TypeVar

from guardrails import Guard
from pydantic import BaseModel

from app.config import settings
from app.guardrails.validators import (
    HarmfulContentDetector,
    PIIDetector,
    PromptInjectionDetector,
    SecretsPresentDetector,
)
from app.monitoring import metrics_store

T = TypeVar("T", bound=BaseModel)

# Maps a validator's class name (as it appears in ValidationSummary.validator_name)
# to the safety event category recorded in metrics_store.
_CATEGORY_BY_VALIDATOR = {
    "PromptInjectionDetector": "prompt_injection",
    "HarmfulContentDetector": "policy_violation",
    "SecretsPresentDetector": "secrets_detected",
    "PIIDetector": "pii_detected",
}

# Which categories are allowed to block the request (raise) vs. just log.
_BLOCKING_SETTINGS = {
    "prompt_injection": lambda: settings.GUARDRAILS_BLOCK_PROMPT_INJECTION,
    "policy_violation": lambda: settings.GUARDRAILS_BLOCK_HARMFUL_CONTENT,
    "secrets_detected": lambda: settings.GUARDRAILS_BLOCK_SECRETS,
    "pii_detected": lambda: False,  # PII is redacted, never blocked
}


class GuardrailBlockedError(Exception):
    """Raised when an input guard detection is configured to block the request."""

    def __init__(self, category: str, details: str):
        self.category = category
        self.details = details
        super().__init__(f"Request blocked by guardrail [{category}]: {details}")


class GuardrailsEngine:
    """Runs input safety validators and output schema validation for the AI routes."""

    def __init__(self):
        # All input validators run in "detect + fix" mode; whether a detection
        # actually blocks the request is decided by this engine (see
        # _BLOCKING_SETTINGS), not by guardrails' own on_fail action. That way
        # every validator always runs and gets logged, even when one of them
        # would otherwise short-circuit the chain by raising.
        self._input_guard = Guard().use(
            PromptInjectionDetector(on_fail="noop"),
            HarmfulContentDetector(on_fail="noop"),
            SecretsPresentDetector(on_fail="fix"),
            PIIDetector(on_fail="fix"),
        )
        self._output_guards: dict[type[BaseModel], Guard] = {}

    def check_input(self, text: str, task_type: str) -> str:
        """Runs all input guards against `text`.

        Records a safety event for every detection, redacts secrets/PII in
        the text that will actually be sent to the model, and raises
        GuardrailBlockedError if a detected category is configured to block.

        Returns the (possibly redacted) text to forward to the LLM.
        """
        result = self._input_guard.validate(text)
        sanitized = result.validated_output if isinstance(result.validated_output, str) else text

        block: tuple[str, str] | None = None
        for summary in result.validation_summaries:
            category = _CATEGORY_BY_VALIDATOR.get(summary.validator_name, "unknown")
            metrics_store.record_safety_event(
                event_type=category,
                task_type=task_type,
                input_text_snippet=text,
                details=summary.failure_reason,
            )
            if block is None and _BLOCKING_SETTINGS.get(category, lambda: False)():
                block = (category, summary.failure_reason)

        if block is not None:
            category, details = block
            raise GuardrailBlockedError(category, details)

        return sanitized

    def validate_output(self, raw_text: str, model_class: type[T], task_type: str = "unknown") -> T:
        """Validates a raw LLM response string against `model_class`'s schema
        (required fields, types, ranges, allowed enum values) using
        `Guard.for_pydantic`, replacing hand-rolled JSON parsing.
        """
        guard = self._output_guards.get(model_class)
        if guard is None:
            guard = Guard.for_pydantic(output_class=model_class)
            self._output_guards[model_class] = guard

        result = guard.parse(llm_output=raw_text)
        if not result.validation_passed:
            raise RuntimeError(f"Failed to parse AI response as JSON: {raw_text}")

        return model_class(**result.validated_output)


guardrails_engine = GuardrailsEngine()
