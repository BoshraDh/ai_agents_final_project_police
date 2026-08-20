"""Gmail API sender (OAuth2, `gmail.send` scope only).

Emails the four mandatory JSON report artifacts to the grader address.
Obtaining the OAuth2 credential (creating a Google Cloud project, enabling
the Gmail API, downloading `credentials.json`, and running the one-time
browser consent flow that produces `token.json`) is a live, guided setup
the user runs herself — this module only *consumes* an existing
`token.json`, it never tries to obtain one unattended. See
`docs/PRD_reporting_shell.md`.
"""

from __future__ import annotations

import base64
from collections.abc import Callable
from email.message import EmailMessage
from pathlib import Path
from typing import Any

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def build_message(
    recipient: str, subject: str, body: str, attachments: list[Path]
) -> dict[str, str]:
    """Builds a Gmail API `messages.send` body — a base64url-encoded MIME message."""
    message = EmailMessage()
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)
    for path in attachments:
        message.add_attachment(
            path.read_bytes(), maintype="application", subtype="json", filename=path.name
        )
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
    return {"raw": raw}


def _default_service_factory(token_path: Path) -> Any:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    credentials = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    return build("gmail", "v1", credentials=credentials)


def send_report(
    token_path: Path,
    recipient: str,
    subject: str,
    body: str,
    attachments: list[Path],
    service_factory: Callable[[Path], Any] = _default_service_factory,
) -> dict[str, Any]:
    """Sends the message; returns the Gmail API's response dict."""
    service = service_factory(token_path)
    message = build_message(recipient, subject, body, attachments)
    return service.users().messages().send(userId="me", body=message).execute()
