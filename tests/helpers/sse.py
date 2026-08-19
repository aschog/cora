"""Reading a server-sent-event stream, for whoever is on the receiving end of one."""

import json


def frames(body: str) -> list[tuple[str, dict]]:
    """The stream as the (event, data) pairs it carried, in order."""
    return [_parsed(frame) for frame in body.split("\n\n") if frame.strip()]


def _parsed(frame: str) -> tuple[str, dict]:
    name, data = "", "null"
    for line in frame.splitlines():
        field, _, value = line.partition(": ")
        if field == "event":
            name = value
        elif field == "data":
            data = value
    return name, json.loads(data)
