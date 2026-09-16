EXTRACTION_REFUSED = (
    "I can't reveal or change my instructions. Ask me something about your "
    "interview preparation instead."
)
LIVE_REFUSED = (
    "I won't answer for you in an interview that is happening now — that is the "
    "moment the practice was for. Bring me the question afterwards and we'll drill it."
)

_PROMPT = (
    "system prompt",
    "your instructions",
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
_WANTS_THE_ANSWER = (
    "answer",
    "what should i say",
    "what do i say",
    "solve",
    "respond",
)


def refuse_misuse(question: str) -> str | None:
    """Refuses the two misuses of a coach: being made to hand over its instructions,
    and being made to sit the interview instead of the candidate.

    A cheap first pass over the clear phrasings, deliberately: it runs ahead of the
    model on every message, so it stays a word list. What it misses, the style's own
    ground rules are there to catch — and cora's security plugin holds the system-wide
    injection screen, so this one only knows interviews.
    """
    text = question.lower()
    if _any(text, _OVERRIDES) or (_any(text, _PROMPT) and _any(text, _TAMPER)):
        return EXTRACTION_REFUSED
    if _any(text, _HAPPENING_NOW) and _any(text, _WANTS_THE_ANSWER):
        return LIVE_REFUSED
    return None


def _any(text: str, phrases: tuple[str, ...]) -> bool:
    return any(phrase in text for phrase in phrases)
