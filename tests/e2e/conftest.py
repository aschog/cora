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
def model() -> str | None:
    """The companion seam to `credentials`: stub-model is a deliberate tripwire
    (a live call would reject it), so the live module overrides this to None and
    the app falls back to the composition root's shipped default."""
    return "stub-model"


@pytest.fixture
def app(
    page: Page,
    credentials: tuple[str, str],
    model: str | None,
    tmp_path: Path,
) -> Iterator[Page]:
    base_url, api_key = credentials
    with running_app(
        base_url=base_url, api_key=api_key, db_path=tmp_path / "chroma", model=model
    ) as server:
        page.goto(server.url)
        wait_for_rerun(page)
        yield page
