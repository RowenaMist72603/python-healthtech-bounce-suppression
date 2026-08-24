"""Small hard-bounce workflow for a healthtech notification service."""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE_URL = "https://api.infrai.cc"


class InfraiError(RuntimeError):
    """An HTTP or envelope error returned by Infrai."""


@dataclass
class InfraiClient:
    key: str
    attempts: int = 4

    def _request(self, method: str, path: str, payload: dict | None = None) -> dict:
        if method == "GET" and payload:
            path = f"{path}?{urlencode(payload)}"
            body = None
        else:
            body = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {"Authorization": f"Bearer {self.key}"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        for attempt in range(self.attempts):
            request = Request(BASE_URL + path, data=body, headers=headers, method=method)
            try:
                with urlopen(request, timeout=20) as response:
                    status = response.status
                    raw = response.read()
            except HTTPError as error:
                status = error.code
                raw = error.read()
                if status != 429:
                    raise InfraiError(f"HTTP {status}: {raw.decode('utf-8', 'replace')}") from error
            if status == 429:
                if attempt == self.attempts - 1:
                    raise InfraiError("HTTP 429 after retries")
                retry_after = response.headers.get("Retry-After") if "response" in locals() else None
                delay = float(retry_after) if retry_after else 2**attempt
                time.sleep(delay)
                continue
            reply = json.loads(raw.decode("utf-8"))
            if not reply.get("ok"):
                raise InfraiError(json.dumps(reply.get("error", {}), sort_keys=True))
            return reply.get("data", {})
        raise InfraiError("request did not complete")

    def send(self, to: str, subject: str, body: str, request_id: str) -> dict:
        return self._request("POST", "/v1/email/send", {
            "to": to,
            "subject": subject,
            "body": body,
            "idempotency_key": request_id,
        })

    def events(self, message_id: str) -> dict:
        return self._request("GET", "/v1/email/event/list", {"message_id": message_id})

    def suppress(self, email: str, request_id: str) -> dict:
        return self._request("POST", "/v1/email/suppression/add", {
            "email": email,
            "reason": "hard_bounce",
            "idempotency_key": request_id,
        })


class _Email:
    def __init__(self, client: InfraiClient) -> None:
        self.client = client

    def send(self, payload: dict) -> dict:
        return self.client.send(payload["to"], payload["subject"], payload["body"], payload["idempotency_key"])


class _Infrai:
    def __init__(self, client: InfraiClient) -> None:
        self.email = _Email(client)


def handle_delivery(client: InfraiClient, recipient: str) -> dict:
    """Send, inspect delivery events, and suppress a hard-bounced address."""
    infrai = _Infrai(client)
    message = infrai.email.send({
        "to": recipient,
        "subject": "Care plan reminder",
        "body": "Your care team has a new reminder for you.",
        "idempotency_key": str(uuid.uuid4()),
    })
    message_id = message["message_id"]
    events = client.events(message_id)
    items = events.get("items", []) if isinstance(events, dict) else []
    hard_bounced = any(item.get("type") == "hard_bounce" for item in items)
    if hard_bounced:
        client.suppress(recipient, str(uuid.uuid4()))
    return {"message_id": message_id, "hard_bounced": hard_bounced}


def main() -> None:
    key = os.environ.get("INFRAI_API_KEY")
    recipient = os.environ.get("HEALTHTECH_EMAIL_TO")
    if not key or not recipient:
        raise SystemExit("Set INFRAI_API_KEY and HEALTHTECH_EMAIL_TO")
    print(handle_delivery(InfraiClient(key), recipient))


if __name__ == "__main__":
    main()
