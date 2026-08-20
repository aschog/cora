import pathlib

import pytest

import gen_reference
import workspace

LAID_OUT = (
    "cora/domain/__init__.py",
    "cora/domain/errors.py",
    "cora/domain/_working_notes.py",
    "cora/adapters/__init__.py",
    "cora/adapters/chroma_retriever.py",
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
    assert [name for name in _named(src) if "adapters" in name] == []


@pytest.mark.integration
def test_the_reference_landing_page_lists_every_module(built: pathlib.Path) -> None:
    listed = (built / "api" / "index.html").read_text()
    missing = [
        ".".join(parts)
        for parts, _ in gen_reference.reference_pages(workspace.ROOT / "src")
        if f'href="{"/".join(parts)}/"' not in listed
    ]
    assert missing == []


@pytest.mark.integration
def test_no_nav_file_is_shipped_as_a_page(built: pathlib.Path) -> None:
    assert sorted(p.name for p in (built / "api").glob("SUMMARY*")) == []
