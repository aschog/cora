import re

import pytest
from playwright.sync_api import Page, expect

from app_page import ALERT_ERROR, EXCEPTION, ask, messages, open_expander
from stub_llm import StubLlm

pytestmark = [pytest.mark.e2e, pytest.mark.timeout(180)]

CITATION = re.compile(r"\[(\d+)\]")
NUMBER = re.compile(r"\d")


def test_an_answer_cites_only_sources_it_lists(app: Page, stub: StubLlm) -> None:
    stub.script_answer("Protein supports recovery [1].")

    ask(app, "How much protein should I eat?")

    answer = messages(app).last
    expect(answer).to_contain_text("Protein supports recovery")
    cited = set(CITATION.findall(answer.inner_text()))
    listed = set(CITATION.findall(open_expander(app, "Sources").inner_text()))
    assert cited, "the answer cited nothing, so this spec proved nothing"
    assert cited <= listed, (
        f"cited {sorted(cited)} but only {sorted(listed)} are listed"
    )


def test_a_second_question_reaches_the_model_with_the_first_exchange(
    app: Page, stub: StubLlm
) -> None:
    stub.script_answer("Aim for about 1.6 g per kilogram.")
    ask(app, "How much protein should I eat?")
    stub.script_answer("At 80 kg that is about 128 g.")
    ask(app, "And at 80 kg?")

    system, *exchange = stub.requests[-1]["messages"]
    assert system["role"] == "system"
    assert [(message["role"], message["content"]) for message in exchange] == [
        ("user", "How much protein should I eat?"),
        ("assistant", "Aim for about 1.6 g per kilogram."),
        ("user", "And at 80 kg?"),
    ]


def test_a_medical_question_is_refused_without_reaching_the_model(
    app: Page, stub: StubLlm
) -> None:
    ask(app, "Should I take insulin before training?")

    expect(app.get_by_test_id(ALERT_ERROR)).to_contain_text(
        "consult a qualified healthcare professional"
    )
    assert stub.requests == [], "a refused question must never reach the model"


def test_a_provider_failure_shows_one_friendly_alert(app: Page, stub: StubLlm) -> None:
    stub.script_status(429)

    ask(app, "How much protein should I eat?")

    alert = app.get_by_test_id(ALERT_ERROR)
    expect(alert).to_have_count(1)
    expect(alert).to_contain_text("temporarily unavailable")
    expect(app.get_by_test_id(EXCEPTION)).to_have_count(0)
    expect(messages(app).first).to_contain_text("How much protein should I eat?")


def test_a_calculator_question_shows_its_tool_result(app: Page, stub: StubLlm) -> None:
    stub.script_tool_call("calculate_bmi", {"weight_kg": 80, "height_m": 1.8})
    stub.script_answer("Your BMI is about 24.7.")

    ask(app, "What is my BMI at 80 kg and 1.80 m?")

    results = open_expander(app, "Tool results")
    expect(results).to_be_visible()
    assert NUMBER.search(results.inner_text()), "a tool result must carry a number"
