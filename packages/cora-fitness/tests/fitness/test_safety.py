import pytest

from cora.core.errors import InputRejectedError
from cora.plugins.fitness.safety import MedicalSafetyRule


def test_medication_dosage_question_is_redirected() -> None:
    with pytest.raises(InputRejectedError) as excinfo:
        MedicalSafetyRule().apply("What steroid dosage should I take?")

    message = excinfo.value.user_message.lower()
    assert "medical" in message
    assert "professional" in message


def test_medical_condition_question_is_redirected() -> None:
    with pytest.raises(InputRejectedError):
        MedicalSafetyRule().apply("Do I have diabetes?")


@pytest.mark.parametrize(
    "text",
    ["DIABETES", "Is my pregnancy affecting my macros?"],
)
def test_matching_is_case_insensitive_and_stem_based(text: str) -> None:
    with pytest.raises(InputRejectedError):
        MedicalSafetyRule().apply(text)


def test_benign_fitness_question_passes() -> None:
    MedicalSafetyRule().apply("How much protein should I eat to build muscle?")


@pytest.mark.parametrize(
    "text",
    [
        "How much protein should I eat to build muscle?",
        "What dose of creatine should I take?",
        "How much caffeine should I have before training?",
    ],
)
def test_in_scope_supplement_questions_are_allowed(text: str) -> None:
    MedicalSafetyRule().apply(text)
