import os
import pathlib
import re
import subprocess
import sys

import pytest

import workspace

pytestmark = pytest.mark.integration

QUIET_FORK = {
    "NO_MKDOCS_2_WARNING": "true",
    "DISABLE_MKDOCS_2_WARNING": "true",
}


RENDERED = ("domain", "ports", "engine", "app")
NARRATIVE = ("big-picture", "happy-path")


def _rendered_modules() -> list[str]:
    root = workspace.ROOT / "src" / "cora"
    found = []
    for package in RENDERED:
        for path in sorted((root / package).rglob("*.py")):
            parts = ("cora", *path.relative_to(root).with_suffix("").parts)
            if parts[-1] == "__init__":
                parts = parts[:-1]
            if any(part.startswith("_") for part in parts[1:]):
                continue
            found.append(".".join(parts))
    return found


def _reference_page(built: pathlib.Path, dotted: str) -> pathlib.Path:
    return built.joinpath("api", *dotted.split(".")) / "index.html"


def _drawings(page: str) -> set[str]:
    written = (workspace.ROOT / "docs" / f"{page}.md").read_text()
    return set(re.findall(r"\]\((assets/[^)]+)\)", written))


def test_the_site_holds_the_narrative_pages_and_a_generated_page_per_rendered_module(
    tmp_path: pathlib.Path,
) -> None:
    built = tmp_path / "site"
    build = subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "--strict", "--site-dir", str(built)],
        cwd=workspace.ROOT,
        capture_output=True,
        text=True,
        env={**os.environ, **QUIET_FORK},
    )
    assert build.returncode == 0, build.stderr

    assert [
        name for name in NARRATIVE if (built / name / "index.html").is_file()
    ] == list(NARRATIVE)

    for name in NARRATIVE:
        assert _drawings(name), f"{name} shows no drawing"
        assert all((built / asset).is_file() for asset in _drawings(name))

    modules = _rendered_modules()
    assert [
        dotted for dotted in modules if _reference_page(built, dotted).is_file()
    ] == modules

    assert sorted(str(p) for p in (workspace.ROOT / "docs" / "api").rglob("*.md")) == []
