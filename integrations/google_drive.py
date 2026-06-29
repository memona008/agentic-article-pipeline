from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaInMemoryUpload

from config import GOOGLE_TOKEN_FILE, require_google_credentials

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def _get_credentials() -> Credentials:
    creds = None
    token_path = Path(GOOGLE_TOKEN_FILE)
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        client_secrets = require_google_credentials()
        flow = InstalledAppFlow.from_client_secrets_file(client_secrets, SCOPES)
        creds = flow.run_local_server(port=0)
    token_path.write_text(creds.to_json(), encoding="utf-8")
    return creds


def create_google_doc(title: str, body: str) -> str:
    creds = _get_credentials()
    service = build("drive", "v3", credentials=creds)
    metadata = {"name": title, "mimeType": "application/vnd.google-apps.document"}
    media = MediaInMemoryUpload(body.encode("utf-8"), mimetype="text/plain", resumable=True)
    created = (
        service.files()
        .create(body=metadata, media_body=media, fields="id, webViewLink")
        .execute()
    )
    url = created.get("webViewLink") or f"https://docs.google.com/document/d/{created['id']}/edit"
    print(f"Google Drive: created Google Doc '{title}' -> {url}")
    return url
