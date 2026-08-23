import json
import pathlib

import pytest

import gen_reference
import workspace

LAID_OUT = (
    "cora/domain/__init__.py",
    "cora/domain/errors.py",
    "cora/domain/_working_notes.py",
    "cora/domain/_working/__init__.py",
    "cora/domain/_working/notes.py",
    "cora/ports/deep/__init__.py",
    "cora/ports/deep/thing.py",
    "cora/adapters/__init__.py",
    "cora/adapters/chroma_retriever.py",
    "cora/plugins/fitness/tools.py",
    "cora/frontends/react/api.py",
)


@pytest.fixture
def src(tmp_path: pathlib.Path) -> pathlib.Path:
    for relative in LAID_OUT:
        module = tmp_path / relative
        module.parent.mkdir(parents=True, exist_ok=True)
        module.write_text("")
    return tmp_path


def _named(src: pathlib.Path) -> list[str]:
    return [".".join(parts) for parts, _ in gen_reference.reference_pages(src)]


def _pages(src: pathlib.Path) -> dict[str, str]:
    return {
        ".".join(parts): str(page) for parts, page in gen_reference.reference_pages(src)
    }


def test_a_private_module_gets_no_page(src: pathlib.Path) -> None:
    assert [name for name in _named(src) if "_working_notes" in name] == []


def test_a_packages_init_becomes_the_packages_own_page(src: pathlib.Path) -> None:
    assert _pages(src)["cora.domain"] == "api/cora/domain/index.md"
    assert "cora.domain.__init__" not in _named(src)


def test_a_module_gets_a_page_of_its_own(src: pathlib.Path) -> None:
    assert _pages(src)["cora.domain.errors"] == "api/cora/domain/errors/index.md"


def test_only_the_rendered_packages_get_pages(src: pathlib.Path) -> None:
    outside = ("adapters", "plugins", "frontends")
    assert [name for name in _named(src) if any(o in name for o in outside)] == []


def test_a_module_inside_a_private_package_gets_no_page(src: pathlib.Path) -> None:
    assert [name for name in _named(src) if "_working" in name] == []


def test_a_module_inside_a_public_subpackage_gets_one(src: pathlib.Path) -> None:
    named = _named(src)
    assert "cora.ports.deep" in named
    assert "cora.ports.deep.thing" in named


@pytest.mark.integration
def test_a_module_page_is_titled_by_its_dotted_name(built: pathlib.Path) -> None:
    page = built / "api" / "cora" / "domain" / "errors" / "index.html"
    assert "<title>cora.domain.errors - cora</title>" in page.read_text()


@pytest.mark.integration
def test_search_names_every_module_by_its_dotted_name(built: pathlib.Path) -> None:
    index = json.loads((built / "search" / "search_index.json").read_text())
    titled = {entry["title"] for entry in index["docs"] if "#" not in entry["location"]}
    assert "Index" not in titled, "a page titled by its filename is unfindable"
    missing = [
        ".".join(parts)
        for parts, _ in gen_reference.reference_pages(workspace.ROOT / "src")
        if ".".join(parts) not in titled
    ]
    assert missing == []
