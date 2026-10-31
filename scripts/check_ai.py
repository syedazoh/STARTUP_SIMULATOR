"""Run from backend/: python ../scripts/check_ai.py. Prints no credentials."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from pydantic import BaseModel
from app.config import settings
from app.core.llm import get_groq_llm
from app.core.llm_errors import report_llm_failure


class Probe(BaseModel):
    ok: bool


async def check():
    print(f"Environment file: {Path('.env').resolve()}")
    configured = bool(
        settings.groq_api_key and settings.groq_api_key != "your-groq-api-key"
    )
    print(f"Groq key configured: {configured}")
    # Print model identifiers, not arbitrary environment values that could be a key.
    if settings.groq_model in {
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "llama-3.3-70b-versatile",
        "qwen/qwen3.8-27b",
    }:
        print(f"Model: {settings.groq_model}")
    else:
        print("Model: custom model (inspect GROQ_MODEL locally)")
    try:
        result = await asyncio.wait_for(
            get_groq_llm()
            .with_structured_output(Probe)
            .ainvoke("Return ok=true as a structured response."),
            timeout=30,
        )
        if not result.ok:
            raise ValueError("Probe did not return success")
    except Exception as exc:
        failure = report_llm_failure("diagnostic", exc)
        print(f"AI check FAILED [{failure.code}]: {failure.message}")
        return 1
    print("AI check PASSED: structured model response received.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(check()))
