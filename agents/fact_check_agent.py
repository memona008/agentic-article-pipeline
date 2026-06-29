import sys
from pathlib import Path

from pydantic_ai import Agent
from pydantic_ai.capabilities import WebSearch
from pydantic_ai.models.openai import OpenAIResponsesModel

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import require_openai_api_key
from models.schemas import FactCheckResult
from prompts.prompts import FACT_CHECK_PROMPT

require_openai_api_key()

fact_check_agent = Agent[str, FactCheckResult](
    model=OpenAIResponsesModel(model_name="gpt-4.1-mini"),
    name="FactCheckAgent",
    description="An AI agent that checks facts.",
    system_prompt=FACT_CHECK_PROMPT,
    deps_type=str,
    output_type=FactCheckResult,
    capabilities=[WebSearch()],
)


def check_topic_truth(user_prompt: str) -> FactCheckResult:
    return fact_check_agent.run_sync(user_prompt).output
