from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from docchat.errors import InputRejectedError

_REDIRECT = (
    "I can't help with medical or medication questions. Please consult a "
    "qualified healthcare professional."
)

_KEYWORDS: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "medication": ("dosage", "dose", "steroid", "insulin", "prescription"),
        "medical": (
            "diabetes",
            "blood pressure",
            "heart condition",
            "thyroid",
            "pregnan",
        ),
    }
)


@dataclass(frozen=True)
class MedicalSafetyRule:
    keywords: Mapping[str, tuple[str, ...]] = _KEYWORDS
    message: str = _REDIRECT

    def apply(self, user_input: str) -> None:
        text = user_input.lower()
        for group in self.keywords.values():
            if any(keyword in text for keyword in group):
                raise InputRejectedError(self.message)
