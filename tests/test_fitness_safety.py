import pytest

from docchat.errors import InputRejectedError
from docchat_plugins.fitness.safety import MedicalSafetyRule


def test_medication_dosage_question_is_redirected() -> None:
    with pytest.raises(InputRejectedError) as excinfo:
        MedicalSafetyRule().apply("What steroid dosage should I take?")

    message = excinfo.value.user_message.lower()
    assert "medical" in message
    assert "professional" in message


def test_medical_condition_question_is_redirected() -> None:
    with pytest.raises(InputRejectedError):
        MedicalSafetyRule().apply("Do I have diabetes?")
