import os
from collections.abc import Callable, Generator
from contextlib import contextmanager
from functools import wraps
from typing import Any, TypeVar

import config  # noqa: F401 — ensures .env is loaded before reading Langfuse env vars

if not os.getenv("LANGFUSE_BASE_URL") and os.getenv("LANGFUSE_HOST"):
    os.environ.setdefault("LANGFUSE_BASE_URL", os.environ["LANGFUSE_HOST"])

LANGFUSE_BASE_URL = os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")

_configured = False
_client = None

T = TypeVar("T")


class _NoOpSpan:
    def update(self, **kwargs: Any) -> None:
        pass


@contextmanager
def trace_step(name: str) -> Generator[Any, None, None]:
    """Langfuse span for a single pipeline step. No-ops when Langfuse is not configured."""
    if not _configured or _client is None:
        yield _NoOpSpan()
        return

    with _client.start_as_current_observation(as_type="span", name=name) as span:
        yield span


def trace_workflow(fn: Callable[[str], T]) -> Callable[[str], T]:
    """Decorator for the root pipeline trace with tags and explicit input."""

    @wraps(fn)
    def wrapper(user_prompt: str) -> T:
        if not _configured or _client is None:
            return fn(user_prompt)

        from langfuse import observe, propagate_attributes

        @observe(name="article_workflow", capture_input=False, capture_output=False)
        def _traced(prompt: str) -> T:
            _client.update_current_span(input={"user_prompt": prompt})
            with propagate_attributes(
                tags=["agentflow", "article-workflow"],
                metadata={"feature": "article-pipeline"},
            ):
                return fn(prompt)

        return _traced(user_prompt)

    return wrapper


def update_workflow_span(**kwargs: Any) -> None:
    """Update the root workflow span output. No-ops when Langfuse is not configured."""
    if _configured and _client is not None:
        _client.update_current_span(**kwargs)


def configure_observability() -> bool:
    """Configure Langfuse tracing for pydantic-ai agents. Returns True if enabled."""
    global _configured, _client
    if _configured:
        return True

    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    if not public_key or not secret_key:
        print("Langfuse not configured (missing LANGFUSE_PUBLIC_KEY/SECRET_KEY); skipping observability.")
        return False

    from langfuse import get_client
    from pydantic_ai import Agent

    _client = get_client()
    if not _client.auth_check():
        print("Langfuse authentication failed. Check LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, and LANGFUSE_BASE_URL.")
        return False

    Agent.instrument_all()
    _configured = True
    print("Langfuse observability enabled.")
    return True


def flush_observability() -> None:
    """Flush pending Langfuse traces. Call before short-lived processes exit."""
    if _configured and _client is not None:
        _client.flush()
