import pytest

from cora.domain.errors import InputRejectedError
from cora.plugins.fitness.safety import MedicalSafetyRule


@pytest.mark.parametrize(
    "text",
    [
        "What steroid dosage should I take?",
        "Should I stop taking my blood pressure medication?",
        "Can I get a prescription for insulin?",
    ],
)
def test_a_medication_question_is_redirected(text: str) -> None:
    with pytest.raises(InputRejectedError) as excinfo:
        MedicalSafetyRule().apply(text)

    message = excinfo.value.user_message.lower()
    assert "medical" in message
    assert "professional" in message


@pytest.mark.parametrize(
    "text",
    [
        "Do I have diabetes?",
        "Are these symptoms of a thyroid problem?",
        "DO I HAVE DIABETES?",
    ],
)
def test_asking_for_a_diagnosis_is_redirected(text: str) -> None:
    with pytest.raises(InputRejectedError):
        MedicalSafetyRule().apply(text)


@pytest.mark.parametrize(
    "text",
    [
        "I have diabetes, how should I train?",
        "Is my pregnancy affecting my macros?",
        "My blood pressure is high — which lifts should I avoid?",
    ],
)
def test_naming_a_condition_is_not_asking_about_it(text: str) -> None:
    """A condition is context for a training question, not a request for a diagnosis.
    Refusing the whole message turns the guard rail into the reason the app is useless
    to the people most in need of a careful answer; the caveat is the plugin's to
    write."""
    MedicalSafetyRule().apply(text)


@pytest.mark.parametrize(
    "text",
    [
        "How much protein should I eat to build muscle?",
        "What dose of creatine should I take?",
        "How much caffeine should I have before training?",
    ],
)
def test_in_scope_questions_are_allowed(text: str) -> None:
    MedicalSafetyRule().apply(text)
