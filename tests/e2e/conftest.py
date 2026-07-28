from collections.abc import Iterator
from pathlib import Path

import pytest
from playwright.sync_api import Page

from app_page import wait_for_rerun
from app_server import running_app
from stub_llm import StubLlm

WIDE = {"width": 1280, "height": 720}


@pytest.fixture(scope="session")
def browser_context_args(
    browser_context_args: dict[str, object],
) -> dict[str, object]:
    # Streamlit collapses the sidebar on a narrow viewport, so --device="Pixel 5"
    # would otherwise hide content the specs assert on.
    return {**browser_context_args, "viewport": WIDE}


@pytest.fixture
def stub() -> Iterator[StubLlm]:
    with StubLlm() as stub:
        yield stub


@pytest.fixture
def credentials(stub: StubLlm) -> tuple[str, str]:
    """The live/stub strategy: parametrise this to return real OpenRouter values
    and every spec below runs against a real model unchanged."""
    return stub.base_url, "dummy-key"


@pytest.fixture
def app(page: Page, credentials: tuple[str, str], tmp_path: Path) -> Iterator[Page]:
    base_url, api_key = credentials
    with running_app(
        base_url=base_url, api_key=api_key, db_path=tmp_path / "chroma"
    ) as server:
        page.goto(server.url)
        wait_for_rerun(page)
        yield page
