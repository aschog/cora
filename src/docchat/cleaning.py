import re

_BLANK_LINES = re.compile(r"\n{3,}")


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _BLANK_LINES.sub("\n\n", text)
    return text.strip()
