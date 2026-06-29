import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", str(BASE_DIR / "credentials.json"))
GOOGLE_TOKEN_FILE = os.getenv("GOOGLE_TOKEN_FILE", str(BASE_DIR / "token.json"))


def _load_env_file() -> None:
    if not ENV_FILE.exists():
        return

    for raw_line in ENV_FILE.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env_file()


def require_openai_api_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_ADMIN_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing OpenAI credentials. Set OPENAI_API_KEY (or OPENAI_ADMIN_KEY) in your shell or in .env"
        )
    os.environ["OPENAI_API_KEY"] = api_key
    return api_key


def require_google_credentials() -> str:
    credentials_path = Path(GOOGLE_CREDENTIALS_FILE)
    if not credentials_path.exists():
        raise RuntimeError(
            f"Missing Google OAuth client secrets at {credentials_path}. "
            "Download an OAuth client (Desktop app) from Google Cloud Console."
        )
    return str(credentials_path)
