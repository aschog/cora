from cora.core.errors import InputRejectedError

_REDIRECT = (
    "I can't help with medical or medication questions. Please consult a "
    "qualified healthcare professional."
)

_KEYWORDS = {
    "medication": ("medication", "prescription", "steroid", "insulin"),
    "medical": (
        "diabetes",
        "blood pressure",
        "heart condition",
        "thyroid",
        "pregnan",
    ),
}


class MedicalSafetyRule:
    def apply(self, user_input: str) -> None:
        text = user_input.lower()
        for group in _KEYWORDS.values():
            if any(keyword in text for keyword in group):
                raise InputRejectedError(_REDIRECT)
