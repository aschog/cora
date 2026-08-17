from cora.domain.errors import InputRejectedError

_REDIRECT = (
    "I can't help with medical or medication questions. Please consult a "
    "qualified healthcare professional."
)

_MEDICATIONS = ("medication", "prescription", "steroid", "insulin")

_CONDITIONS = ("diabet", "blood pressure", "heart condition", "thyroid", "pregnan")

_DIAGNOSIS_REQUESTS = (
    "do i have",
    "have i got",
    "diagnos",
    "symptom",
    "should i be worried",
)


class MedicalSafetyRule:
    """Refuses a request for medical judgement, not a mention of a condition: naming
    diabetes to explain what a training answer has to work around is the question this
    plugin exists to answer, and the caveat it earns is the model's to write."""

    def apply(self, user_input: str) -> None:
        text = user_input.lower()
        names_a_condition = any(word in text for word in _CONDITIONS)
        asks_for_a_diagnosis = any(word in text for word in _DIAGNOSIS_REQUESTS)
        about_medication = any(word in text for word in _MEDICATIONS)
        if about_medication or (names_a_condition and asks_for_a_diagnosis):
            raise InputRejectedError(_REDIRECT)
