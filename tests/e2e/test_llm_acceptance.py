import os
import re

import pytest
from playwright.sync_api import Page, expect

from app_page import EXCEPTION, MARKDOWN, ask, messages, open_expander
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

    results = open_expander(app, "Tool results").inner_text()
    assert NUMBER.search(results), f"a real tool call must carry a number: {results!r}"
    assert not TOOL_ERROR.search(results), f"the tool did not run: {results!r}"

    expect(app.get_by_test_id(EXCEPTION)).to_have_count(0)
