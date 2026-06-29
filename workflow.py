from kitaru import checkpoint, flow

from agents.article_agent import revise_article, write_article
from agents.fact_check_agent import check_topic_truth
from agents.feedback_agent import review_article
from agents.publish_agent import publish_article
from integrations.langfuse import trace_step, trace_workflow, update_workflow_span
from models.schemas import ArticleDraft, FactCheckResult, FeedbackResult, PublishResult


@checkpoint
def step_fact_check(user_prompt: str) -> FactCheckResult:
    return check_topic_truth(user_prompt)


@checkpoint
def step_write_article(fact: FactCheckResult) -> ArticleDraft:
    return write_article(fact)


@checkpoint
def step_review_article(draft: ArticleDraft) -> FeedbackResult:
    return review_article(draft)


@checkpoint
def step_revise_article(
    fact: FactCheckResult,
    draft: ArticleDraft,
    feedback: FeedbackResult,
) -> ArticleDraft:
    return revise_article(fact, draft, feedback)


@checkpoint
def step_publish_article(draft: ArticleDraft, feedback: FeedbackResult) -> PublishResult:
    return publish_article(draft)


@flow
def article_workflow(user_prompt: str) -> str:
    return _run_workflow_body(user_prompt)


@trace_workflow
def _run_workflow_body(user_prompt: str) -> str:
    with trace_step("fact_check") as span:
        fact_ref = step_fact_check(user_prompt)
        fact = fact_ref.load()
        span.update(
            output={
                "topic": fact.topic,
                "is_true": fact.is_true,
                "confidence": fact.confidence,
            }
        )

    if not fact.is_true:
        status = f"Rejected: {fact.topic} (confidence={fact.confidence})"
        update_workflow_span(
            output={"status": "rejected", "topic": fact.topic, "confidence": fact.confidence}
        )
        print(status)
        return status

    with trace_step("write_article") as span:
        draft_ref = step_write_article(fact_ref)
        draft = draft_ref.load()
        span.update(output={"topic": draft.topic, "reference_count": len(draft.references)})

    with trace_step("review_article") as span:
        feedback_ref = step_review_article(draft_ref)
        feedback = feedback_ref.load()
        span.update(
            output={
                "approved": feedback.approved,
                "comment_count": len(feedback.comments),
                "summary": feedback.summary,
            }
        )

    attempts = 1
    while not feedback.approved and attempts < 3:
        with trace_step(f"revise_article_attempt_{attempts + 1}") as span:
            draft_ref = step_revise_article(fact_ref, draft_ref, feedback_ref)
            draft = draft_ref.load()
            span.update(output={"topic": draft.topic, "attempt": attempts + 1})

        with trace_step(f"review_article_attempt_{attempts + 1}") as span:
            feedback_ref = step_review_article(draft_ref)
            feedback = feedback_ref.load()
            span.update(
                output={
                    "approved": feedback.approved,
                    "comment_count": len(feedback.comments),
                    "attempt": attempts + 1,
                }
            )
        attempts += 1
        print(f"Attempt {attempts}: {feedback.approved}")

    if not feedback.approved:
        status = f"Not approved after {attempts} rounds; not publishing."
        update_workflow_span(
            output={
                "status": "not_approved",
                "attempts": attempts,
                "comments": feedback.comments,
            }
        )
        print(status)
        print("Outstanding comments:", feedback.comments)
        return status

    with trace_step("publish_article") as span:
        result = step_publish_article(draft_ref, feedback_ref).load()
        span.update(
            output={
                "status": result.status,
                "google_doc_url": result.google_doc_url,
                "slack_ok": result.slack_ok,
            }
        )

    update_workflow_span(
        output={"status": "published", "google_doc_url": result.google_doc_url}
    )
    print(result.status)
    return result.status


def run_workflow(user_prompt: str) -> str:
    return article_workflow.run(user_prompt=user_prompt).wait()
