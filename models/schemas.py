from pydantic import BaseModel, Field, HttpUrl


class FactCheckResult(BaseModel):
    topic: str = Field(description="The topic of the claim to be fact-checked")
    is_true: bool = Field(description="Whether the claim is true or false")
    confidence: float = Field(description="The confidence in the fact-check")
    evidence: list[str] = Field(description="The evidence for the fact-check")
    references: list[HttpUrl] = Field(description="The references URLs for the fact-check")


class ArticleDraft(BaseModel):
    topic: str = Field(description="The topic of the article")
    article: str = Field(description="The article to be written")
    references: list[HttpUrl] = Field(description="The references URLs for the article")


class FeedbackResult(BaseModel):
    approved: bool = Field(description="True only if the draft is ready to publish")
    comments: list[str] = Field(description="Actionable feedback points to address")
    summary: str = Field(description="One-line overall assessment")


class ArticleContext(BaseModel):
    fact_check: FactCheckResult
    previous_draft: ArticleDraft | None = None
    feedback: FeedbackResult | None = None


class PublishResult(BaseModel):
    google_doc_url: str | None = Field(default=None, description="URL of the created Google Doc")
    slack_ok: bool = Field(default=False, description="Whether the Slack message was sent")
    status: str = Field(description="Human-readable publish confirmation")
