import uuid

import requests

from .settings import SETTINGS


def add_todo(text: str, note: str) -> None:
    request = requests.post(
        "https://api.todoist.com/sync/v9/quick/add",
        headers={
            "Authorization": f"Bearer {SETTINGS.todoist.key}",
            "X-Request-Id": str(uuid.uuid4()),
        },
        json={"text": text, "note": note},
        timeout=5,
    )
    request.raise_for_status()
