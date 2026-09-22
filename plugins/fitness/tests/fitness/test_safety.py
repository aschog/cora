import pytest

from cora.plugins.fitness.safety import refuse_medical


@pytest.mark.parametrize(
    "text",
    [
        "What steroid dosage should I take?",
        "Should I stop taking my blood pressure medication?",
        "Can I get a prescription for insulin?",
        "Should I increase my thyroid medication before a heavy week?",
    ],
)
def test_a_decision_about_medication_is_redirected(text: str) -> None:
    refused = refuse_medical(text)

    assert refused is not None
    assert "medical" in refused.lower()
    assert "professional" in refused.lower()


@pytest.mark.parametrize(
    "text",
    [
        "Do I have diabetes?",
        "Are these symptoms of a thyroid problem?",
        "My blood sugar keeps crashing, is that diabetes?",
        "Could I be pregnant?",
        "Is my chest pain a heart condition?",
        "Am I diabetic?",
        "DO I HAVE DIABETES?",
    ],
)
def test_asking_for_a_diagnosis_is_redirected(text: str) -> None:
    assert refuse_medical(text) is not None


@pytest.mark.parametrize(
    "text",
    [
        "What should I do about my thyroid?",
        "How do I treat my blood pressure?",
        "Can training cure my diabetes?",
    ],
)
def test_asking_to_be_treated_is_redirected(text: str) -> None:
    assert refuse_medical(text) is not None


@pytest.mark.parametrize(
    "text",
    [
        "I have diabetes, how should I train?",
        "Is my pregnancy affecting my macros?",
        "My blood pressure is high — which lifts should I avoid?",
        "I'm on blood pressure medication — what cardio is safe for me?",
        "I have a heart condition, how many sets should I do?",
        "I have diabetes, am I training enough?",
        "I have diabetes — is that a problem for creatine?",
    ],
)
def test_naming_what_you_live_with_is_not_asking_about_it(text: str) -> None:
    assert refuse_medical(text) is None


@pytest.mark.parametrize(
    "text",
    [
        "How much protein should I eat to build muscle?",
        "What dose of creatine should I take?",
        "How much caffeine should I have before training?",
    ],
)
def test_in_scope_questions_are_allowed(text: str) -> None:
    assert refuse_medical(text) is None
