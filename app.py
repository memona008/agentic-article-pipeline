from config import require_openai_api_key
from integrations.langfuse import configure_observability, flush_observability
from workflow import run_workflow

require_openai_api_key()
configure_observability()

if __name__ == "__main__":
    try:
        user_prompt = "Write a 50 words paragraph about the job market in Finland 2026"
        run_workflow(user_prompt)
    finally:
        flush_observability()
