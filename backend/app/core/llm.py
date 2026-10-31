"""Groq LLM client factory, shared by every agent's LangGraph graph"""
from functools import lru_cache

from langchain_groq import ChatGroq

from ..config import settings
from .llm_errors import LLMNotConfiguredError


class UnconfiguredLLM:
    """Keep infrastructure/auth usable without inventing provider credentials."""
    def with_structured_output(self, schema):
        return self

    async def ainvoke(self, prompt):
        raise LLMNotConfiguredError("Configure GROQ_API_KEY to enable AI responses")


@lru_cache(maxsize=8)
def _cached_groq_llm(temperature: float) -> ChatGroq | UnconfiguredLLM:
    if not settings.groq_api_key or settings.groq_api_key == "your-groq-api-key":
        return UnconfiguredLLM()
    return ChatGroq(
        groq_api_key=settings.groq_api_key,
        model_name=settings.groq_model,
        temperature=temperature,
    )


def get_groq_llm(temperature: float = 0.0) -> ChatGroq | UnconfiguredLLM:
    # ChatGroq construction has real fixed cost (~1-1.5s here, mostly
    # httpx/cert-store setup) — caching means the 5 agents per business (6
    # ChatGroq instances, CEO needs 2) share one client instead of each
    # paying that cost, which otherwise makes lazy per-business agent
    # construction (AgentRegistry.get_or_create) visibly slow on a new
    # business's first request. Safe to share: with_structured_output()
    # returns a new bound runnable, it doesn't mutate the base model.
    return _cached_groq_llm(temperature)
