import pathlib
import subprocess
import sys

import pytest

import workspace

pytestmark = [
    pytest.mark.integration,
    pytest.mark.xfail(strict=True, reason="story 25: the diagrams do not render yet"),
]

RENDERED = ("domain", "ports", "engine", "app")
NARRATIVE = ("big-picture", "happy-path")


def _rendered_modules() -> list[str]:
    root = workspace.ROOT / "src" / "cora"
    found = []
    for package in RENDERED:
        for path in sorted((root / package).glob("*.py")):
            if path.stem.startswith("_") and path.name != "__init__.py":
                continue
            parts = (
                ("cora", package)
                if path.name == "__init__.py"
                else ("cora", package, path.stem)
            )
            found.append(".".join(parts))
    return found


def _reference_page(built: pathlib.Path, dotted: str) -> pathlib.Path:
    return built.joinpath("api", *dotted.split(".")) / "index.html"


def _fenced_diagrams(page: str) -> int:
    return (workspace.ROOT / "docs" / f"{page}.md").read_text().count("```mermaid")


def test_the_site_holds_the_narrative_pages_and_a_generated_page_per_rendered_module(
    tmp_path: pathlib.Path,
) -> None:
    built = tmp_path / "site"
    build = subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "--strict", "--site-dir", str(built)],
        cwd=workspace.ROOT,
        capture_output=True,
        text=True,
    )
    assert build.returncode == 0, build.stderr

    assert [
        name for name in NARRATIVE if (built / name / "index.html").is_file()
    ] == list(NARRATIVE)

    drawn = {
        name: (built / name / "index.html").read_text().count('class="mermaid"')
        for name in NARRATIVE
    }
    assert drawn == {name: _fenced_diagrams(name) for name in NARRATIVE}

    modules = _rendered_modules()
    assert [
        dotted for dotted in modules if _reference_page(built, dotted).is_file()
    ] == modules

    assert sorted(str(p) for p in (workspace.ROOT / "docs" / "api").rglob("*.md")) == []
