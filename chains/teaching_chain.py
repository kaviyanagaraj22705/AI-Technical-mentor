import logging
from langchain_core.output_parsers import StrOutputParser
from chains.llm import get_llm, LLMConnectionError, safe_parse_json
from prompts.templates import TEACHING_PROMPT
from utils.validators import validate_topic

logger = logging.getLogger(__name__)


def run_teaching_chain(topic: str) -> str:
    validate_topic(topic)
    try:
        llm = get_llm(temperature=0.7)
        chain = TEACHING_PROMPT | llm | StrOutputParser()
        result = chain.invoke({"topic": topic})
        return result
    except LLMConnectionError:
        raise
    except Exception as exc:
        logger.exception("Teaching chain failed")
        raise LLMConnectionError(f"Teaching chain error: {exc}") from exc
