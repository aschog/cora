import pathlib
import re
import subprocess
from html.parser import HTMLParser

import pytest

import workspace
from site_config import config as _config
from site_config import nav_pages as _nav_pages

NARRATIVE = ("big-picture", "happy-path")
NARRATIVE_PAGES = tuple(f"{name}.md" for name in NARRATIVE)


def test_both_narrative_pages_are_in_the_nav() -> None:
    pages = _nav_pages(_config()["nav"])
    assert [name for name in NARRATIVE_PAGES if name in pages] == list(NARRATIVE_PAGES)


def test_the_built_site_is_not_tracked() -> None:
    ignored = subprocess.run(
        ["git", "check-ignore", "site/"],
        cwd=workspace.ROOT,
        capture_output=True,
        text=True,
    )
    assert ignored.returncode == 0, (
        "the built site must be ignored, not reviewed as source"
    )


REMOTE = re.compile(r"(?:https?:)?//[A-Za-z0-9.-]+")
# `a` is a link the reader chooses to follow, not something the page loads.
# `xmlns` names an XML namespace, which is not fetched either.
FOLLOWED = frozenset({"a"})
NOT_FETCHED = frozenset({"xmlns"})


# A parser, not a pattern: a hand-written one stopped reading a tag at its first
# boolean attribute, so `<script defer src=…>` and any single-quoted value went by.
class _Loaded(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.remote: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in FOLLOWED:
            return
        for name, value in attrs:
            if value and name.split(":")[0] not in NOT_FETCHED:
                self.remote.extend(REMOTE.findall(value))


def _asset_urls(page: pathlib.Path) -> list[str]:
    parser = _Loaded()
    parser.feed(page.read_text())
    return parser.remote


@pytest.mark.integration
def test_no_page_loads_an_asset_from_another_host(built: pathlib.Path) -> None:
    remote = {
        url
        for page in built.rglob("*.html")
        for url in _asset_urls(page)
        if url.startswith(("http://", "https://", "//"))
    }
    assert remote == set(), "the site has to render with the network off"


SHOWN = re.compile(r"\]\((assets/[^)]+)\)")


def _shown(page: str) -> set[str]:
    return set(SHOWN.findall((workspace.ROOT / "docs" / f"{page}.md").read_text()))


@pytest.mark.integration
def test_every_drawing_a_page_shows_is_built_beside_it(built: pathlib.Path) -> None:
    shown = {name: _shown(name) for name in NARRATIVE}
    assert all(shown.values()), "a narrative page with no drawing on it"

    missing = [
        asset
        for assets in shown.values()
        for asset in sorted(assets)
        if not (built / asset).is_file()
    ]
    assert missing == [], f"the site does not ship {missing}"
