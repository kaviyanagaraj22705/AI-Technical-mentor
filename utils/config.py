import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH, override=False)


def get_env(key: str, default: str | None = None) -> str | None:
    return os.getenv(key, default)


OPENROUTER_API_KEY = get_env("OPENROUTER_API_KEY")
OPENROUTER_MODEL = get_env("OPENROUTER_MODEL", "openrouter/auto")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

LANGSMITH_TRACING = get_env("LANGSMITH_TRACING", "false").lower() == "true"
LANGSMITH_API_KEY = get_env("LANGSMITH_API_KEY")
LANGSMITH_PROJECT = get_env("LANGSMITH_PROJECT", "AI-Technical-Mentor")

DATABASE_PATH = BASE_DIR / "learning_mentor.db"


def validate_openrouter_config() -> list[str]:
    errors: list[str] = []
    if not OPENROUTER_API_KEY:
        errors.append("OPENROUTER_API_KEY is not set in .env")
    if not OPENROUTER_MODEL:
        errors.append("OPENROUTER_MODEL is not set in .env")
    return errors


def validate_langsmith_config() -> list[str]:
    warnings: list[str] = []
    if LANGSMITH_TRACING and not LANGSMITH_API_KEY:
        warnings.append("LANGSMITH_TRACING is true but LANGSMITH_API_KEY is not set")
    return warnings
