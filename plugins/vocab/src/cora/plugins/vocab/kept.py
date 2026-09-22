"""The two things everything this plugin keeps goes through: read back, and written.

Both of its stored values are one JSON object under one name — the schedule and which
side is German — and both wanted the same answer to unreadable text. Written once, so
the day that answer changes it changes once.
"""

import json
from typing import Any


def read_object(written: str | None) -> dict[str, Any]:
    """The object this text holds, or an empty one where it holds no readable object.

    Unreadable text reads as nothing kept. What is lost is something the reader can
    say again, and refusing would strand the plugin behind a file nobody can see until
    somebody deletes it by hand.
    """
    try:
        read = json.loads(written or "{}")
    except ValueError:
        return {}
    return read if isinstance(read, dict) else {}


def as_text(held: dict[str, Any]) -> str:
    """This object, as the text to keep. Sorted, so one value is one text."""
    return json.dumps(held, sort_keys=True)
