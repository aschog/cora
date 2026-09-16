import re

EXTRACTION_REFUSED = (
    "I can't reveal or change my instructions. Ask me something about your "
    "interview preparation instead."
)
LIVE_REFUSED = (
    "I won't answer for you in an interview that is happening now — that is the "
    "moment the practice was for. Bring me the question afterwards and we'll drill it."
)

# What a tamper verb has to be reaching for, and reaching for *cora's own*: a candidate
# rewriting somebody else's system prompt as a take-home is the subject, not the misuse.
_OURS = (
    "your system prompt",
    "your prompt",
    "your instructions",
    "your initial instructions",
    "the system prompt",
    "initial instructions",
    "developer message",
)
_TAMPER = (
    "reveal",
    "show",
    "print",
    "repeat",
    "ignore",
    "disregard",
    "override",
    "forget",
    "leak",
    "rewrite",
    "what are",
)
# Adjacent, not merely both present: the two word lists as a cross-product refuse
# "show me how to talk about system prompt design", which is the field itself.
_EXTRACTION = re.compile(
    rf"\b(?:{'|'.join(_TAMPER)})\b[^.?!]{{0,12}}?(?:{'|'.join(_OURS)})"
)

_OVERRIDES = ("ignore all previous", "disregard all previous", "jailbreak")

_HAPPENING_NOW = (
    "interview right now",
    "in an interview now",
    "interviewer just asked",
    "interviewer is asking",
    "mid-interview",
    "currently in an interview",
    "live interview right now",
)
# Asking to be handed the answer, not the word "answer": somebody saying they froze
# mid-interview and gave a weak answer is describing practice, and wants it drilled.
_WANTS_THE_ANSWER = (
    "what should i say",
    "what do i say",
    "answer it for me",
    "answer this for me",
    "answer for me",
    "solve it for me",
    "solve this for me",
    "tell me the answer",
    "give me the answer",
)


def refuse_misuse(question: str) -> str | None:
    """Refuses the two misuses of a coach: being made to hand over its instructions,
    and being made to sit the interview instead of the candidate.

    A cheap first pass over the clear phrasings, deliberately: it runs ahead of the
    model on every message, so it stays phrases rather than a model of its own. What it
    misses, the style's own ground rules are there to catch — and cora's security plugin
    holds the system-wide injection screen, so this one only knows interviews. It is
    tuned to miss rather than to refuse: a refusal ends the turn, and the people it
    would end it on are the ones interviewing for the jobs whose vocabulary it reads.
    """
    text = question.lower()
    if _any(text, _OVERRIDES) or _EXTRACTION.search(text):
        return EXTRACTION_REFUSED
    if _any(text, _HAPPENING_NOW) and _any(text, _WANTS_THE_ANSWER):
        return LIVE_REFUSED
    return None


def _any(text: str, phrases: tuple[str, ...]) -> bool:
    return any(phrase in text for phrase in phrases)
