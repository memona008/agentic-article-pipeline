import sys
from pathlib import Path

from pydantic_ai import Agent, RunContext
from pydantic_ai.capabilities import WebSearch
from pydantic_ai.models.openai import OpenAIResponsesModel

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import require_openai_api_key
from models.schemas import ArticleContext, ArticleDraft, FactCheckResult, FeedbackResult
from prompts.prompts import ARTICLE_PROMPT

require_openai_api_key()

article_agent = Agent[ArticleContext, ArticleDraft](
    model=OpenAIResponsesModel(model_name="gpt-4.1-mini"),
    name="ArticleAgent",
    description="Writes a draft article from a verified topic.",
    system_prompt=ARTICLE_PROMPT,
    deps_type=ArticleContext,
    output_type=ArticleDraft,
    capabilities=[WebSearch()],
)


@article_agent.instructions
def article_context(ctx: RunContext[ArticleContext]) -> str:
    fc = ctx.deps.fact_check
    refs = "\n".join(f"- {url}" for url in fc.references)
    evidence = "\n".join(f"- {e}" for e in fc.evidence)
    parts = [
        f"Verified topic: {fc.topic}",
        f"Confidence: {fc.confidence}",
        f"Evidence:\n{evidence}",
        f"Fact-check references (use these first):\n{refs}",
    ]

    if ctx.deps.previous_draft is not None and ctx.deps.feedback is not None:
        prev = ctx.deps.previous_draft
        fb = ctx.deps.feedback
        comments = "\n".join(f"- {c}" for c in fb.comments)
        parts.extend(
            [
                f"Previous draft:\n{prev.article}",
                f"Feedback summary: {fb.summary}",
                f"Comments to address:\n{comments}",
            ]
        )

    return "\n\n".join(parts)


def write_article(fact_check: FactCheckResult) -> ArticleDraft:
    if not fact_check.is_true:
        raise ValueError(f"Cannot write article for unverified topic: {fact_check.topic}")
    ctx = ArticleContext(fact_check=fact_check)
    return article_agent.run_sync(
        "Write the first draft from the verified topic.",
        deps=ctx,
    ).output


def revise_article(
    fact_check: FactCheckResult,
    previous_draft: ArticleDraft,
    feedback: FeedbackResult,
) -> ArticleDraft:
    ctx = ArticleContext(
        fact_check=fact_check,
        previous_draft=previous_draft,
        feedback=feedback,
    )
    return article_agent.run_sync(
        "Revise the draft to address the feedback.",
        deps=ctx,
    ).output
