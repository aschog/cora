from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

from app_page import CHAT_INPUT, EXCEPTION, SIDEBAR, ask, messages, sources
from stub_llm import StubLlm

pytestmark = [pytest.mark.e2e, pytest.mark.timeout(180)]


def test_the_app_loads_with_its_shell_rendered(app: Page) -> None:
    expect(app.get_by_test_id(CHAT_INPUT)).to_be_visible()
    expect(app.get_by_test_id(SIDEBAR)).to_be_visible()
    expect(app.get_by_text("Documents")).to_be_visible()
    expect(app.get_by_test_id(EXCEPTION)).to_have_count(0)


def test_a_page_load_ingests_the_seed_docs_under_the_configured_path(
    app: Page, tmp_path: Path
) -> None:
    expect(sources(app).filter(has_text="protein.md")).to_have_count(1)

    assert any((tmp_path / "chroma").iterdir())


def test_the_barrier_returns_only_after_the_rerun_finished(
    app: Page, stub: StubLlm
) -> None:
    stub.script_answer("Deadlifts train the posterior chain.")
    stub.script_delay(1.5)

    ask(app, "What do deadlifts train?")

    # Deliberately not expect(): a retrying assertion would hide a barrier that
    # returned early. count() is the only way to catch it.
    assert messages(app).count() == 2
