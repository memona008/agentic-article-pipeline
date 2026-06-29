import sys
from pathlib import Path

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIResponsesModel

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import require_openai_api_key
from models.schemas import ArticleDraft, FeedbackResult
from prompts.prompts import FEEDBACK_PROMPT

require_openai_api_key()

feedback_agent = Agent[ArticleDraft, FeedbackResult](
    model=OpenAIResponsesModel(model_name="gpt-4.1-mini"),
    name="FeedbackAgent",
    description="Reviews a draft article and decides if it is publishable.",
    system_prompt=FEEDBACK_PROMPT,
    deps_type=ArticleDraft,
    output_type=FeedbackResult,
)


@feedback_agent.instructions
def article_to_review(ctx: RunContext[ArticleDraft]) -> str:
    draft = ctx.deps
    refs = "\n".join(f"- {url}" for url in draft.references)
    return (
        f"Topic: {draft.topic}\n\n"
        f"Article:\n{draft.article}\n\n"
        f"References:\n{refs}"
    )


def review_article(draft: ArticleDraft) -> FeedbackResult:
    return feedback_agent.run_sync("Review this draft.", deps=draft).output
