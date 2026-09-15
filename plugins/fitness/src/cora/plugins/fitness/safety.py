import re

_REDIRECT = (
    "I can't help with medical or medication questions. Please consult a "
    "qualified healthcare professional."
)

_CONDITIONS = ("diabet", "blood pressure", "heart condition", "thyroid", "pregnan")
_MEDICATIONS = ("medication", "prescription", "steroid", "insulin")

_ABOUT_MEDICATION = (
    "should i take",
    "should i stop",
    "stop taking",
    "start taking",
    "dose",
    "dosage",
    "prescri",
    "increase my",
    "switch to",
)
_FOR_TREATMENT = ("treat", "cure", "what should i do about")
_FOR_A_VERDICT = ("diagnos", "symptom", "should i be worried")

_CONDITION = "|".join(_CONDITIONS)
_ASKING = (
    "do i have",
    "did i have",
    "have i got",
    "could i be",
    "could it be",
    "am i",
    "is (?:that|this|it)",
)
_ASKS_TO_BE_DIAGNOSED = re.compile(
    rf"\b(?:{'|'.join(_ASKING)})\b[^?]{{0,30}}?(?:{_CONDITION})"
)
_ASKS_IF_IT_IS_ONE = re.compile(
    rf"\b(?:is|are|could)\b[^?]*?\ban?\s+(?:\w+\s+){{0,2}}(?:{_CONDITION})"
)


def refuse_medical(question: str) -> str | None:
    """Refuses a request for medical judgement, not a mention of what someone lives
    with: naming diabetes or the medication they take is how a training question gets
    the answer it needs, and the caution that answer carries is the model's to write.

    A cheap first pass over the clear phrasings, deliberately: it runs ahead of the
    model on every message, so it stays a word list. What it misses, the plugin's
    "you are not a doctor" instruction is there to catch.
    """
    text = question.lower()
    subject = _any(text, _CONDITIONS + _MEDICATIONS)
    asks = _any(text, _ABOUT_MEDICATION + _FOR_TREATMENT + _FOR_A_VERDICT)
    diagnosis = _ASKS_TO_BE_DIAGNOSED.search(text) or _ASKS_IF_IT_IS_ONE.search(text)
    if (subject and asks) or diagnosis:
        return _REDIRECT
    return None


def _any(text: str, words: tuple[str, ...]) -> bool:
    return any(word in text for word in words)
