from typing import Any


def validate_not_empty(value: str, field_name: str) -> str:
    if value is None or not str(value).strip():
        raise ValueError(f"{field_name} cannot be empty")
    return str(value).strip()


def validate_score(value: Any, field_name: str) -> int:
    try:
        score = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be an integer")
    if score < 0 or score > 10:
        raise ValueError(f"{field_name} must be between 0 and 10")
    return score


def validate_topic(topic: str) -> str:
    return validate_not_empty(topic, "Topic")


def validate_difficulty(difficulty: str) -> str:
    allowed = {"beginner", "intermediate", "advanced"}
    if difficulty.lower() not in allowed:
        raise ValueError(f"Difficulty must be one of: {', '.join(sorted(allowed))}")
    return difficulty.lower()


def validate_answer(answer: str) -> str:
    return validate_not_empty(answer, "Answer")
