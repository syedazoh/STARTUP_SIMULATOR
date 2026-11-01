"""Allowlisted AI diagnostics; never expose provider messages, bodies or prompts."""

import logging
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

logger = logging.getLogger(__name__)


class LLMNotConfiguredError(RuntimeError):
    pass


class LLMBusyError(RuntimeError):
    status_code = 429

    def __init__(self, retry_after_seconds=1):
        super().__init__("AI request queue or provider cooldown is busy")
        self.retry_after_seconds = retry_after_seconds


# Unrecognized strings are never copied to logs or API responses.
PROVIDER_CODES = frozenset({
    "model_decommissioned", "model_not_found", "tool_use_failed",
    "json_validate_failed", "context_length_exceeded", "invalid_api_key",
    "rate_limit_exceeded", "invalid_request_error", "invalid_value",
    "unsupported_parameter", "unsupported_value",
})
PROVIDER_PARAMS = frozenset({
    "messages", "response_format", "response_format.json_schema", "tools",
    "tool_choice", "max_tokens", "max_completion_tokens", "temperature",
})


def safe_provider_details(error):
    body = getattr(error, "body", None)
    detail = body.get("error", body) if isinstance(body, dict) else {}
    if not isinstance(detail, dict):
        return None, None
    code, param = detail.get("code"), detail.get("param")
    return (
        code if isinstance(code, str) and code in PROVIDER_CODES else None,
        param if isinstance(param, str) and param in PROVIDER_PARAMS else None,
    )


def retry_after_seconds(error):
    value = getattr(error, "retry_after_seconds", None)
    if value is None:
        response = getattr(error, "response", None)
        headers = getattr(response, "headers", {})
        value = headers.get("retry-after")
    if value is None:
        return None
    try:
        delay = float(value)
    except (ValueError, TypeError):
        try:
            when = parsedate_to_datetime(str(value))
            if when.tzinfo is None:
                when = when.replace(tzinfo=timezone.utc)
            delay = (when - datetime.now(timezone.utc)).total_seconds()
        except (ValueError, TypeError, OverflowError):
            return None
    return max(0.0, delay) if math.isfinite(delay) else None


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
    "connection": "The server could not reach the AI service or the request timed out. Please try again later.",
    "provider_error": "The AI service is temporarily unavailable. Please try again later.",
    "invalid_response": "The AI service could not produce a valid response. Please try again.",
    "invalid_request": "The AI service rejected the request configuration. The platform operator needs to check the safe AI diagnostics.",
    "context_length": "The AI conversation is too long for the configured model. Please shorten the request or start a new conversation.",
    "structured_output": "The AI service could not produce the required structured response. No action was created from this response.",
}


def classify_llm_error(error: Exception) -> LLMFailure:
    if isinstance(error, LLMCallFailed):
        return error.failure
    status = getattr(error, "status_code", None)
    provider_code, _ = safe_provider_details(error)
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
    elif provider_code == "context_length_exceeded":
        code = "context_length"
    elif provider_code in ("tool_use_failed", "json_validate_failed"):
        code = "structured_output"
    elif status == 400:
        code = "invalid_request"
    elif isinstance(error, (ConnectionError, TimeoutError)) or type(error).__name__ in (
        "APIConnectionError", "APITimeoutError",
    ):
        code = "connection"
    elif isinstance(status, int) and status >= 500:
        code = "provider_error"
    else:
        code = "invalid_response"
    message = MESSAGES[code]
    retry = retry_after_seconds(error)
    if code == "rate_limit" and retry is not None:
        message += f" Retry after {math.ceil(retry)} seconds."
    return LLMFailure(code, message)


class LLMCallFailed(RuntimeError):
    """Signals that the shared bounded attempt budget is exhausted.

    Department graphs must not wrap it in another round of retries.
    Only allowlisted provider attributes survive this boundary.
    """
    def __init__(self, error):
        super().__init__("AI request did not complete successfully")
        self.failure = classify_llm_error(error)
        self.status_code = getattr(error, "status_code", None)
        code, param = safe_provider_details(error)
        self.body = {"error": {"code": code, "param": param}}
        self.retry_after_seconds = retry_after_seconds(error)


def report_llm_failure(operation: str, error: Exception) -> LLMFailure:
    failure = classify_llm_error(error)
    status = getattr(error, "status_code", None)
    provider_code, param = safe_provider_details(error)
    logger.warning(
        "AI operation=%s failed category=%s status=%s type=%s provider_code=%s param=%s",
        operation, failure.code, status if isinstance(status, int) else None,
        type(error).__name__, provider_code, param,
    )
    return failure
