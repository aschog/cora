from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

from app_page import ALERT_ERROR, CHAT_INPUT, EXCEPTION, wait_for_rerun
from app_server import running_app
from stub_llm import StubLlm

pytestmark = [pytest.mark.e2e, pytest.mark.timeout(180)]


def test_a_server_started_without_an_api_key_says_so_instead_of_chatting(
    page: Page, stub: StubLlm, tmp_path: Path
) -> None:
    # Own process, not the `app` fixture: config is read once at startup and
    # `st.cache_resource` holds it for the life of the process.
    with running_app(
        base_url=stub.base_url, api_key=None, db_path=tmp_path / "chroma"
    ) as server:
        page.goto(server.url)
        wait_for_rerun(page)

        expect(page.get_by_test_id(ALERT_ERROR)).to_contain_text(
            "OPENROUTER_API_KEY is not set"
        )
        expect(page.get_by_test_id(CHAT_INPUT)).to_have_count(0)
        expect(page.get_by_test_id(EXCEPTION)).to_have_count(0)
