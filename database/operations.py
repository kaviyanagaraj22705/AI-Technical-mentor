from datetime import datetime
from typing import Any
from database.db import get_connection


def create_session(topic: str, difficulty: str) -> int:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO learning_sessions (topic, difficulty, status) VALUES (?, ?, ?)",
            (topic, difficulty, "started"),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def save_topic_explanation(session_id: int, explanation: str) -> int:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO topic_explanations (session_id, explanation) VALUES (?, ?)",
            (session_id, explanation),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def save_scenario(
    session_id: int, title: str, description: str, difficulty: str
) -> int:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO scenarios (session_id, scenario_title, scenario_description, difficulty) VALUES (?, ?, ?, ?)",
            (session_id, title, description, difficulty),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def save_student_answer(session_id: int, answer_text: str) -> int:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO student_answers (session_id, answer_text) VALUES (?, ?)",
            (session_id, answer_text),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def save_evaluation(
    session_id: int,
    total_score: int,
    technical_score: int,
    conceptual_score: int,
    practical_score: int,
    strengths: str,
    weaknesses: str,
    missing_concepts: str,
    corrected_explanation: str,
    suggested_answer: str,
    recommendations: str,
) -> int:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO evaluations
            (session_id, total_score, technical_score, conceptual_score, practical_score,
             strengths, weaknesses, missing_concepts, corrected_explanation,
             suggested_answer, recommendations)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                total_score,
                technical_score,
                conceptual_score,
                practical_score,
                strengths,
                weaknesses,
                missing_concepts,
                corrected_explanation,
                suggested_answer,
                recommendations,
            ),
        )
        cur.execute(
            "UPDATE learning_sessions SET status = 'completed', updated_at = datetime('now') WHERE id = ?",
            (session_id,),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def get_all_sessions() -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT ls.id, ls.topic, ls.difficulty, ls.status, ls.created_at, ls.updated_at,
                   e.total_score, e.technical_score, e.conceptual_score, e.practical_score
            FROM learning_sessions ls
            LEFT JOIN evaluations e ON e.session_id = ls.id
            ORDER BY ls.id DESC
            """
        )
        rows = cur.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_session_by_id(session_id: int) -> dict[str, Any] | None:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM learning_sessions WHERE id = ?", (session_id,)
        )
        row = cur.fetchone()
        if row is None:
            return None
        return dict(row)
    finally:
        conn.close()


def get_session_details(session_id: int) -> dict[str, Any] | None:
    session = get_session_by_id(session_id)
    if session is None:
        return None
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM topic_explanations WHERE session_id = ? ORDER BY created_at DESC LIMIT 1",
            (session_id,),
        )
        row = cur.fetchone()
        session["explanation"] = dict(row) if row else None

        cur.execute(
            "SELECT * FROM scenarios WHERE session_id = ? ORDER BY created_at DESC LIMIT 1",
            (session_id,),
        )
        row = cur.fetchone()
        session["scenario"] = dict(row) if row else None

        cur.execute(
            "SELECT * FROM student_answers WHERE session_id = ? ORDER BY submitted_at DESC LIMIT 1",
            (session_id,),
        )
        row = cur.fetchone()
        session["answer"] = dict(row) if row else None

        cur.execute(
            "SELECT * FROM evaluations WHERE session_id = ? ORDER BY evaluated_at DESC LIMIT 1",
            (session_id,),
        )
        row = cur.fetchone()
        session["evaluation"] = dict(row) if row else None

        return session
    finally:
        conn.close()


def get_progress_stats() -> dict[str, Any]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) as total_sessions FROM learning_sessions"
        )
        total_sessions = cur.fetchone()["total_sessions"]

        cur.execute(
            "SELECT COUNT(*) as completed FROM learning_sessions WHERE status = 'completed'"
        )
        completed = cur.fetchone()["completed"]

        cur.execute(
            "SELECT AVG(total_score) as avg_score, MAX(total_score) as max_score FROM evaluations"
        )
        row = cur.fetchone()
        avg_score = row["avg_score"] if row["avg_score"] is not None else 0
        max_score = row["max_score"] if row["max_score"] is not None else 0

        cur.execute(
            """
            SELECT topic, COUNT(*) as count, AVG(e.total_score) as avg_score
            FROM learning_sessions ls
            LEFT JOIN evaluations e ON e.session_id = ls.id
            GROUP BY ls.topic
            ORDER BY count DESC
            """
        )
        topic_performance = [dict(row) for row in cur.fetchall()]

        cur.execute(
            """
            SELECT date(created_at) as day, COUNT(*) as count
            FROM learning_sessions
            GROUP BY date(created_at)
            ORDER BY day DESC
            LIMIT 14
            """
        )
        activity_over_time = [dict(row) for row in cur.fetchall()]

        return {
            "total_sessions": total_sessions,
            "completed": completed,
            "avg_score": round(float(avg_score), 2),
            "max_score": max_score,
            "topic_performance": topic_performance,
            "activity_over_time": activity_over_time,
        }
    finally:
        conn.close()
