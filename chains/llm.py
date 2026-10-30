import json
import logging
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from utils.config import (
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
    OPENROUTER_BASE_URL,
    LANGSMITH_TRACING,
    LANGSMITH_API_KEY,
    LANGSMITH_PROJECT,
    validate_openrouter_config,
    validate_langsmith_config,
)
from utils.validators import validate_topic, validate_difficulty, validate_answer, validate_score

logger = logging.getLogger(__name__)


class LLMConnectionError(Exception):
    pass


def get_llm(temperature: float = 0.7) -> ChatOpenAI:
    errors = validate_openrouter_config()
    if errors:
        raise LLMConnectionError("; ".join(errors))

    if LANGSMITH_TRACING and LANGSMITH_API_KEY:
        import os
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = LANGSMITH_API_KEY
        os.environ["LANGCHAIN_PROJECT"] = LANGSMITH_PROJECT

    return ChatOpenAI(
        model=OPENROUTER_MODEL,
        base_url=OPENROUTER_BASE_URL,
        api_key=OPENROUTER_API_KEY,
        temperature=temperature,
    )


def mask_api_key(api_key: str | None) -> str:
    if not api_key:
        return "not set"
    if len(api_key) <= 8:
        return "***"
    return api_key[:4] + "***" + api_key[-4:]


def safe_parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```json"):
        text = text.removeprefix("```json").removesuffix("```").strip()
    elif text.startswith("```"):
        text = text.removeprefix("```").removesuffix("```").strip()
    return json.loads(text)
