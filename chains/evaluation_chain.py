import logging
import json
from chains.llm import get_llm, LLMConnectionError, safe_parse_json
from prompts.templates import EVALUATION_PROMPT, RECOMMENDATION_PROMPT
from utils.validators import validate_topic, validate_answer, validate_score

logger = logging.getLogger(__name__)


class EvaluationResult:
    def __init__(self, data: dict):
        self.total_score = validate_score(data.get("total_score", 0), "total_score")
        self.technical_score = validate_score(data.get("technical_score", 0), "technical_score")
        self.conceptual_score = validate_score(data.get("conceptual_score", 0), "conceptual_score")
        self.practical_score = validate_score(data.get("practical_score", 0), "practical_score")
        self.strengths = str(data.get("strengths", ""))
        self.weaknesses = str(data.get("weaknesses", ""))
        self.missing_concepts = str(data.get("missing_concepts", ""))
        self.corrected_explanation = str(data.get("corrected_explanation", ""))
        self.suggested_answer = str(data.get("suggested_answer", ""))
        self.recommendations = str(data.get("recommendations", ""))

    def to_dict(self) -> dict:
        return {
            "total_score": self.total_score,
            "technical_score": self.technical_score,
            "conceptual_score": self.conceptual_score,
            "practical_score": self.practical_score,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "missing_concepts": self.missing_concepts,
            "corrected_explanation": self.corrected_explanation,
            "suggested_answer": self.suggested_answer,
            "recommendations": self.recommendations,
        }


def run_evaluation_chain(topic: str, scenario: str, answer: str) -> EvaluationResult:
    validate_topic(topic)
    validate_answer(answer)
    try:
        llm = get_llm(temperature=0.3)
        chain = EVALUATION_PROMPT | llm | StrOutputParser()
        raw = chain.invoke({
            "topic": topic,
            "scenario": scenario,
            "answer": answer,
        })
        data = safe_parse_json(raw)
        return EvaluationResult(data)
    except LLMConnectionError:
        raise
    except (json.JSONDecodeError, ValueError, KeyError) as exc:
        logger.exception("Evaluation parsing failed")
        raise LLMConnectionError(f"Failed to parse evaluation: {exc}") from exc
    except Exception as exc:
        logger.exception("Evaluation chain failed")
        raise LLMConnectionError(f"Evaluation chain error: {exc}") from exc


def generate_recommendations(topic: str, eval_data: dict) -> str:
    try:
        llm = get_llm(temperature=0.7)
        chain = RECOMMENDATION_PROMPT | llm | StrOutputParser()
        result = chain.invoke({
            "topic": topic,
            "total_score": eval_data.get("total_score", 0),
            "technical_score": eval_data.get("technical_score", 0),
            "conceptual_score": eval_data.get("conceptual_score", 0),
            "practical_score": eval_data.get("practical_score", 0),
            "weaknesses": eval_data.get("weaknesses", ""),
            "missing_concepts": eval_data.get("missing_concepts", ""),
        })
        return result
    except LLMConnectionError:
        raise
    except Exception as exc:
        logger.exception("Recommendation chain failed")
        raise LLMConnectionError(f"Recommendation error: {exc}") from exc
