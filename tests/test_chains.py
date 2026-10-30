import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def temp_db_path(tmp_path):
    return tmp_path / "test.db"


def test_database_init_creates_tables(temp_db_path, monkeypatch):
    from database import db as db_module

    monkeypatch.setattr(db_module, "DATABASE_PATH", temp_db_path)
    db_module.init_db()
    assert temp_db_path.exists()

    import sqlite3
    conn = sqlite3.connect(str(temp_db_path))
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cur.fetchall()}
    conn.close()

    expected = {
        "learning_sessions",
        "topic_explanations",
        "scenarios",
        "student_answers",
        "evaluations",
    }
    assert expected.issubset(tables), f"Missing tables: {expected - tables}"


def test_create_and_retrieve_session(temp_db_path, monkeypatch):
    from database import db as db_module
    from database import operations as ops

    monkeypatch.setattr(db_module, "DATABASE_PATH", temp_db_path)
    db_module.init_db()

    sid = ops.create_session("Python", "beginner")
    assert sid == 1

    session = ops.get_session_by_id(sid)
    assert session is not None
    assert session["topic"] == "Python"
    assert session["difficulty"] == "beginner"
    assert session["status"] == "started"


def test_save_and_get_evaluation(temp_db_path, monkeypatch):
    from database import db as db_module
    from database import operations as ops

    monkeypatch.setattr(db_module, "DATABASE_PATH", temp_db_path)
    db_module.init_db()

    sid = ops.create_session("RAG", "intermediate")
    ops.save_student_answer(sid, "I would use embeddings and a vector database.")
    ops.save_evaluation(
        sid,
        total_score=7,
        technical_score=8,
        conceptual_score=7,
        practical_score=6,
        strengths="Good use of embeddings",
        weaknesses="Missing chunking strategy",
        missing_concepts="Text chunking, similarity search",
        corrected_explanation="Use chunking, embeddings, vector DB, similarity search.",
        suggested_answer="Chunk documents, embed them, store in vector DB, query with similarity search.",
        recommendations="Learn chunking and vector databases.",
    )

    detail = ops.get_session_details(sid)
    assert detail is not None
    assert detail["evaluation"] is not None
    assert detail["evaluation"]["total_score"] == 7
    assert detail["answer"] is not None


def test_get_all_sessions_ordering(temp_db_path, monkeypatch):
    from database import db as db_module
    from database import operations as ops

    monkeypatch.setattr(db_module, "DATABASE_PATH", temp_db_path)
    db_module.init_db()

    ops.create_session("Topic A", "beginner")
    ops.create_session("Topic B", "advanced")

    sessions = ops.get_all_sessions()
    assert len(sessions) == 2
    # Most recent first
    assert sessions[0]["topic"] == "Topic B"


def test_progress_stats_empty(temp_db_path, monkeypatch):
    from database import db as db_module
    from database import operations as ops

    monkeypatch.setattr(db_module, "DATABASE_PATH", temp_db_path)
    db_module.init_db()

    stats = ops.get_progress_stats()
    assert stats["total_sessions"] == 0
    assert stats["completed"] == 0
    assert stats["avg_score"] == 0


def test_validate_topic():
    from utils.validators import validate_topic, validate_difficulty, validate_answer

    assert validate_topic("Python") == "Python"
    with pytest.raises(ValueError):
        validate_topic("")
    with pytest.raises(ValueError):
        validate_topic("   ")

    assert validate_difficulty("BEGINNER") == "beginner"
    assert validate_difficulty("Advanced") == "advanced"
    with pytest.raises(ValueError):
        validate_difficulty("expert")

    assert validate_answer("  My answer  ") == "My answer"
    with pytest.raises(ValueError):
        validate_answer("")


def test_chain_construction():
    from chains.teaching_chain import TEACHING_PROMPT  # noqa: F401
    from chains.scenario_chain import SCENARIO_PROMPT  # noqa: F401
    from chains.evaluation_chain import EVALUATION_PROMPT  # noqa: F401
    assert TEACHING_PROMPT is not None
    assert SCENARIO_PROMPT is not None
    assert EVALUATION_PROMPT is not None


def test_evaluation_result_validation():
    from chains.evaluation_chain import EvaluationResult

    result = EvaluationResult({
        "total_score": 8,
        "technical_score": 9,
        "conceptual_score": 8,
        "practical_score": 7,
        "strengths": "Good",
        "weaknesses": "None",
        "missing_concepts": "None",
        "corrected_explanation": "Fine",
        "suggested_answer": "Fine",
        "recommendations": "Keep going",
    })
    assert result.total_score == 8
    d = result.to_dict()
    assert d["total_score"] == 8

    with pytest.raises(ValueError):
        EvaluationResult({"total_score": 15})  # out of range


def test_missing_api_key_raises(monkeypatch):
    from chains import llm as llm_module

    monkeypatch.setattr(llm_module, "OPENROUTER_API_KEY", None)
    monkeypatch.setattr(llm_module, "OPENROUTER_MODEL", "openrouter/auto")
    with pytest.raises(llm_module.LLMConnectionError):
        llm_module.get_llm()


def test_mask_api_key():
    from chains.llm import mask_api_key
    assert mask_api_key(None) == "not set"
    assert mask_api_key("sk-1234567890abcdef") == "sk-1***cdef"
    assert mask_api_key("short") == "***"


def test_safe_parse_json_strips_fences():
    from chains.llm import safe_parse_json
    data = safe_parse_json('```json\n{"a": 1}\n```')
    assert data == {"a": 1}
    data2 = safe_parse_json('{"b": 2}')
    assert data2 == {"b": 2}
