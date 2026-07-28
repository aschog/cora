MAX_LOGGED_CHARS = 120


def truncate(text: str) -> str:
    if len(text) <= MAX_LOGGED_CHARS:
        return text
    return text[: MAX_LOGGED_CHARS - 1] + "…"
