"""The one normalisation a document gets before it is cut up."""

import re

_BLANK_LINES = re.compile(r"\n{3,}")


def clean_text(text: str) -> str:
    """Text with its line endings normalised and its blank runs collapsed.

    This is the text every offset is measured in, so it is what gets kept beside the
    index: a citation into the uploaded bytes would point somewhere else.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _BLANK_LINES.sub("\n\n", text)
    return text.strip()
