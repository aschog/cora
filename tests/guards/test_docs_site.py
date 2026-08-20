import subprocess

import yaml

import workspace

CONFIG = workspace.ROOT / "mkdocs.yml"
NARRATIVE = ("big-picture.md", "happy-path.md")
NOT_THE_PRODUCT = ("sprints/", "cora_mockup.html", "workflow.md")


def _config() -> dict[str, object]:
    return yaml.safe_load(CONFIG.read_text())


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
    assert [name for name in NARRATIVE if name in pages] == list(NARRATIVE)


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
