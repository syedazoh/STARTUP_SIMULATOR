"""Safe diagnostics: never log provider bodies, prompts, headers or credentials."""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class LLMNotConfiguredError(RuntimeError):
    pass


@dataclass(frozen=True)
class LLMFailure:
    code: str
    message: str


MESSAGES = {
    "not_configured": "AI is not configured. The platform operator needs to configure the AI service.",
    "authentication": "The AI service rejected its credentials. The platform operator needs to check them.",
    "permission_denied": "The AI account does not have permission for this request. Contact the platform operator.",
    "model_unavailable": "The configured AI model is unavailable for this account. Contact the platform operator.",
    "rate_limit": "The AI request limit has been reached. Please try again later.",
    "connection": "The server could not reach the AI service. Please try again later.",
    "provider_error": "The AI service is temporarily unavailable. Please try again later.",
    "invalid_response": "The AI service could not produce a valid response. Please try again.",
}


def classify_llm_error(error: Exception) -> LLMFailure:
    status = getattr(error, "status_code", None)
    body = getattr(error, "body", None)
    provider_code = None
    if isinstance(body, dict):
        detail = body.get("error", body)
        if isinstance(detail, dict):
            provider_code = detail.get("code")
    if isinstance(error, LLMNotConfiguredError):
        code = "not_configured"
    elif provider_code in ("model_decommissioned", "model_not_found") or status == 404:
        code = "model_unavailable"
    elif status == 401 or type(error).__name__ == "AuthenticationError":
        code = "authentication"
    elif status == 403:
        code = "permission_denied"
    elif status == 429 or type(error).__name__ == "RateLimitError":
        code = "rate_limit"
    elif isinstance(error, (ConnectionError, TimeoutError)) or type(error).__name__ in (
        "APIConnectionError",
        "APITimeoutError",
    ):
        code = "connection"
    elif isinstance(status, int) and status >= 500:
        code = "provider_error"
    else:
        code = "invalid_response"
    return LLMFailure(code, MESSAGES[code])


def report_llm_failure(operation: str, error: Exception) -> LLMFailure:
    failure = classify_llm_error(error)
    status = getattr(error, "status_code", None)
    logger.warning(
        "AI operation=%s failed category=%s status=%s type=%s",
        operation,
        failure.code,
        status if isinstance(status, int) else None,
        type(error).__name__,
    )
    return failure
