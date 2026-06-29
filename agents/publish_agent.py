import sys
from pathlib import Path

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIResponsesModel

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import require_openai_api_key
from integrations.google_drive import create_google_doc
from integrations.slack import post_slack_message
from models.schemas import ArticleDraft, PublishResult
from prompts.prompts import PUBLISH_PROMPT

require_openai_api_key()

publish_agent = Agent[ArticleDraft, PublishResult](
    model=OpenAIResponsesModel(model_name="gpt-4.1-mini"),
    name="PublishAgent",
    description="Publishes an approved article to Google Drive and Slack.",
    system_prompt=PUBLISH_PROMPT,
    deps_type=ArticleDraft,
    output_type=PublishResult,
)


@publish_agent.tool_plain
def upload_to_google_drive(title: str, content: str) -> str:
    return create_google_doc(title, content)


@publish_agent.tool_plain
def send_to_slack(text: str) -> bool:
    return post_slack_message(text)


@publish_agent.instructions
def article_to_publish(ctx: RunContext[ArticleDraft]) -> str:
    draft = ctx.deps
    return f"Title/topic: {draft.topic}\n\nArticle:\n{draft.article}"


def publish_article(draft: ArticleDraft) -> PublishResult:
    return publish_agent.run_sync("Publish this approved article.", deps=draft).output
