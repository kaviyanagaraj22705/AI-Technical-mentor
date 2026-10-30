import logging
from langchain_core.output_parsers import StrOutputParser
from chains.llm import get_llm, LLMConnectionError
from prompts.templates import SCENARIO_PROMPT
from utils.validators import validate_topic, validate_difficulty

logger = logging.getLogger(__name__)


def run_scenario_chain(topic: str, explanation: str, difficulty: str = "beginner") -> str:
    validate_topic(topic)
    validate_difficulty(difficulty)
    try:
        llm = get_llm(temperature=0.7)
        chain = SCENARIO_PROMPT | llm | StrOutputParser()
        result = chain.invoke({
            "topic": topic,
            "explanation": explanation,
            "difficulty": difficulty,
        })
        return result
    except LLMConnectionError:
        raise
    except Exception as exc:
        logger.exception("Scenario chain failed")
        raise LLMConnectionError(f"Scenario chain error: {exc}") from exc
