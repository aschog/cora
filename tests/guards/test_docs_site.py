import pathlib
import re
import subprocess
from html.parser import HTMLParser

import pytest
import yaml

import workspace
from cora.frontends.react.server import DEFAULT_PORT

CONFIG = workspace.ROOT / "mkdocs.yml"
NARRATIVE = ("big-picture", "happy-path")
NARRATIVE_PAGES = tuple(f"{name}.md" for name in NARRATIVE)
NOT_THE_PRODUCT = ("sprints/", "cora_mockup.html", "workflow.md")


class _Tolerant(yaml.SafeLoader):
    """mkdocs writes `!!python/name:` tags that a safe loader refuses; the guards read
    the config as data and never call what those tags name."""


_Tolerant.add_multi_constructor(
    "tag:yaml.org,2002:python/name:", lambda loader, suffix, node: suffix
)


def _config() -> dict[str, object]:
    return yaml.load(CONFIG.read_text(), Loader=_Tolerant)


def _nav_pages(entry: object) -> list[str]:
    if isinstance(entry, str):
        return [entry]
    if isinstance(entry, dict):
        return [page for value in entry.values() for page in _nav_pages(value)]
    if isinstance(entry, list):
        return [page for item in entry for page in _nav_pages(item)]
    return []


def test_both_narrative_pages_are_in_the_nav() -> None:
    pages = _nav_pages(_config()["nav"])
    assert [name for name in NARRATIVE_PAGES if name in pages] == list(NARRATIVE_PAGES)


def test_build_history_the_mockup_and_the_process_page_are_not_pages() -> None:
    excluded = str(_config()["exclude_docs"]).split()
    assert [name for name in NOT_THE_PRODUCT if name in excluded] == list(
        NOT_THE_PRODUCT
    )


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


def test_the_nav_names_the_reference_once_and_never_a_module() -> None:
    pages = _nav_pages(_config()["nav"])
    assert "api/" in pages, "the reference section is one entry literate-nav resolves"
    assert [page for page in pages if page.startswith("api/") and page != "api/"] == []


MERMAID = workspace.ROOT / "docs" / "assets" / "mermaid-10.2.3.min.js"
REMOTE = re.compile(r"(?:https?:)?//[A-Za-z0-9.-]+")
# `a` is a link the reader chooses to follow, not something the page loads.
# `xmlns` names an XML namespace, which is not fetched either.
FOLLOWED = frozenset({"a"})
NOT_FETCHED = frozenset({"xmlns"})


class _Loaded(HTMLParser):
    """A parser, not a pattern: a hand-written one stopped reading a tag at its first
    boolean attribute, so `<script defer src=…>` and any single-quoted value went by."""

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


def test_the_vendored_mermaid_is_the_version_the_diagrams_are_written_against() -> None:
    assert MERMAID.is_file(), "the diagrams are written against Mermaid 10.2.3"
    assert MERMAID.name in str(_config()["extra_javascript"])
    pinned = MERMAID.name.removeprefix("mermaid-").removesuffix(".min.js")
    assert f'"{pinned}"' in MERMAID.read_text(), (
        "the filename pins the version, so the bundle has to say the same"
    )


@pytest.mark.integration
def test_no_page_loads_an_asset_from_another_host(built: pathlib.Path) -> None:
    remote = {
        url
        for page in built.rglob("*.html")
        for url in _asset_urls(page)
        if url.startswith(("http://", "https://", "//"))
    }
    assert remote == set(), "the site has to render with the network off"


@pytest.mark.integration
def test_every_fenced_diagram_becomes_a_diagram_container(built: pathlib.Path) -> None:
    drawn = {
        name: (built / name / "index.html").read_text().count('class="mermaid"')
        for name in NARRATIVE
    }
    fenced = {
        name: (workspace.ROOT / "docs" / name)
        .with_suffix(".md")
        .read_text()
        .count("```mermaid")
        for name in NARRATIVE
    }
    assert drawn == fenced


@pytest.mark.integration
def test_every_page_with_a_diagram_loads_the_vendored_mermaid(
    built: pathlib.Path,
) -> None:
    unvendored = [
        name
        for name in NARRATIVE
        if MERMAID.name not in (built / name / "index.html").read_text()
    ]
    assert unvendored == [], (
        "without the global, Material fetches mermaid@11 from unpkg"
    )


def _sections() -> dict[str, list[str]]:
    nav = _config()["nav"]
    assert isinstance(nav, list)
    found: dict[str, list[str]] = {}
    for entry in nav:
        if isinstance(entry, dict):
            for title, under in entry.items():
                if str(title) != "Home":
                    found[str(title)] = _nav_pages(under)
    return found


def test_the_front_page_links_every_top_level_section() -> None:
    front = (workspace.ROOT / "docs" / "index.md").read_text()
    unlinked = [
        title
        for title, pages in _sections().items()
        if not any(page in front for page in pages)
    ]
    assert unlinked == []


def test_the_docs_and_the_app_do_not_want_the_same_port() -> None:
    served = re.search(
        r"mkdocs serve[^\n]*--dev-addr[= ]\S*?:(\d+)",
        (workspace.ROOT / "Makefile").read_text(),
    )
    assert served, "`make docs-serve` has to name a port"
    assert int(served.group(1)) != DEFAULT_PORT, (
        "reading the docs while the app runs must not need one of them stopped"
    )


def test_the_site_follows_the_readers_system_theme() -> None:
    theme = _config()["theme"]
    assert isinstance(theme, dict)
    palettes = theme.get("palette")
    assert isinstance(palettes, list)
    by_media: dict[str, object] = {}
    for entry in palettes:
        assert isinstance(entry, dict)
        by_media[str(entry.get("media"))] = entry.get("scheme")
    assert by_media == {
        "(prefers-color-scheme: light)": "default",
        "(prefers-color-scheme: dark)": "slate",
    }


@pytest.mark.integration
def test_both_schemes_reach_the_built_page(built: pathlib.Path) -> None:
    front = (built / "index.html").read_text()
    for scheme, media in (
        ("default", "(prefers-color-scheme: light)"),
        ("slate", "(prefers-color-scheme: dark)"),
    ):
        assert f'data-md-color-scheme="{scheme}"' in front, scheme
        assert f'data-md-color-media="{media}"' in front, media
