import os
import re

import pytest
from playwright.sync_api import Page, expect

from app_page import EXCEPTION, EXPANDER, MARKDOWN, ask, messages, open_expander, upload
from live_llm import live_credentials

pytestmark = [pytest.mark.llm, pytest.mark.timeout(180)]

NUMBER = re.compile(r"\d")
TOOL_ERROR = re.compile(
    r"invalid arguments|unknown tool|returned no result|failed:", re.IGNORECASE
)


@pytest.fixture
def credentials() -> tuple[str, str]:
    """Overrides the conftest stub binding: this module talks to real OpenRouter,
    so no StubLlm ever boots. Missing key skips the whole module."""
    return live_credentials(os.environ)


@pytest.fixture
def model() -> None:
    """Drop the stub-model tripwire: a live call needs the shipped default model."""
    return None


def test_a_real_model_answers_and_calls_a_tool(app: Page) -> None:
    """The one live round-trip. Structural only — a real model's prose is not
    ours to predict, so we assert an answer appeared, a tool actually ran, and
    nothing crashed, never the exact words."""
    ask(app, "What is my BMI at 80 kg and 1.80 m? Use your BMI tool.")

    expect(messages(app).last.get_by_test_id(MARKDOWN).first).to_be_visible()

    trace = open_expander(app, "How I got there").inner_text()
    assert NUMBER.search(trace), f"a real tool call must carry a number: {trace!r}"
    assert not TOOL_ERROR.search(trace), f"the tool did not run: {trace!r}"

    expect(app.get_by_test_id(EXCEPTION)).to_have_count(0)


PROTEIN_DOC = (
    b"# Protein\n\nAim for 1.6 g of protein per kg of bodyweight per day, spread\n"
    b"over three or four meals. Above 2.2 g per kg there is no further benefit.\n"
)


def test_a_real_model_retrieves_for_a_document_question_but_not_for_a_greeting(
    app: Page,
) -> None:
    """The honest proof that retrieval is the model's decision: the same agent,
    two questions, and only one of them reaches the documents. The question never
    says "my documents" — one that does gives the answer away, and the model
    answering a plain domain question from its own knowledge is the bug this
    guards."""
    upload(app, "protein.md", PROTEIN_DOC)

    ask(app, "How much protein should I eat per kg of bodyweight?")

    answered = messages(app).last
    expect(answered.get_by_test_id(MARKDOWN).first).to_be_visible()
    listed = open_expander(app, "Sources").inner_text()
    assert "protein.md" in listed, f"the model answered without retrieving: {listed!r}"

    ask(app, "Hi there!")

    greeted = messages(app).last
    expect(greeted.get_by_test_id(MARKDOWN).first).to_be_visible()
    expect(greeted.get_by_test_id(EXPANDER).filter(has_text="Sources")).to_have_count(0)
    assert "Decided no tool was needed" in greeted.inner_text()
    assert "protein.md" not in greeted.inner_text()
    expect(app.get_by_test_id(EXCEPTION)).to_have_count(0)
