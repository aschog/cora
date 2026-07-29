import os

import pytest
from playwright.sync_api import Page, expect

from app_page import CHAT_INPUT, EXCEPTION
from live_llm import live_credentials

pytestmark = [pytest.mark.llm, pytest.mark.timeout(180)]


@pytest.fixture
def credentials() -> tuple[str, str]:
    """Overrides the conftest stub binding: this module talks to real OpenRouter,
    so no StubLlm ever boots. Missing key skips the whole module."""
    return live_credentials(os.environ)


def test_a_real_model_answers_and_calls_a_tool(app: Page) -> None:
    expect(app.get_by_test_id(CHAT_INPUT)).to_be_visible()
    expect(app.get_by_test_id(EXCEPTION)).to_have_count(0)
