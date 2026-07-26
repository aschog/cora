import ast
import pathlib

import pytest

import cora.core

FORBIDDEN_FRAMEWORKS = frozenset(
    {
        "langchain",
        "langchain_openai",
        "langchain_core",
        "chromadb",
        "sentence_transformers",
        "streamlit",
    }
)
FORBIDDEN_LAYERS = ("cora.adapters", "cora.plugins", "cora.app")

CORE_ROOT = pathlib.Path(cora.core.__file__).parent
SRC_ROOT = CORE_ROOT.parents[1]
CORE_FILES = sorted(CORE_ROOT.rglob("*.py"))
PACKAGE_ROOT = CORE_ROOT.parent
PACKAGE_FILES = sorted(PACKAGE_ROOT.rglob("*.py"))
UI_ROOT = PACKAGE_ROOT / "app" / "ui"


def _package_parts(path: pathlib.Path) -> tuple[str, ...]:
    parts = path.relative_to(SRC_ROOT).with_suffix("").parts
    return parts[:-1]  # drop the module name (or '__init__')


def _resolve(module: str | None, level: int, package_parts: tuple[str, ...]) -> str:
    base = package_parts[: len(package_parts) - (level - 1)]
    return ".".join([*base, module]) if module else ".".join(base)


def _imported_modules(tree: ast.Module, package_parts: tuple[str, ...]):
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0:
                if node.module:
                    yield node.module
            else:
                yield _resolve(node.module, node.level, package_parts)


def _imports_streamlit(path: pathlib.Path) -> bool:
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(
            alias.name.split(".")[0] == "streamlit" for alias in node.names
        ):
            return True
        if (
            isinstance(node, ast.ImportFrom)
            and node.module
            and node.module.split(".")[0] == "streamlit"
        ):
            return True
    return False


def _is_forbidden(module: str) -> bool:
    if module.split(".")[0] in FORBIDDEN_FRAMEWORKS:
        return True
    return any(
        module == layer or module.startswith(f"{layer}.") for layer in FORBIDDEN_LAYERS
    )


def test_core_modules_discovered() -> None:
    assert CORE_FILES, "no cora.core modules discovered — walker is misconfigured"


def test_streamlit_import_is_detected(tmp_path: pathlib.Path) -> None:
    rogue = tmp_path / "rogue.py"
    rogue.write_text("import streamlit as st\n")
    assert _imports_streamlit(rogue)

    innocent = tmp_path / "innocent.py"
    innocent.write_text("import json\n")
    assert not _imports_streamlit(innocent)


@pytest.mark.parametrize(
    "path",
    [p for p in PACKAGE_FILES if not p.is_relative_to(UI_ROOT)],
    ids=lambda p: str(p.relative_to(PACKAGE_ROOT)),
)
def test_streamlit_stays_inside_the_ui_shell(path: pathlib.Path) -> None:
    assert not _imports_streamlit(path), (
        f"{path.relative_to(PACKAGE_ROOT)} imports streamlit outside cora/app/ui"
    )


def test_relative_import_into_outer_layer_is_detected() -> None:
    tree = ast.parse("from ...adapters import chroma_retriever\n")
    pkg = ("cora", "core", "services")
    modules = set(_imported_modules(tree, pkg))
    assert "cora.adapters" in modules
    assert any(_is_forbidden(m) for m in modules)


@pytest.mark.parametrize(
    "path", CORE_FILES, ids=lambda p: str(p.relative_to(CORE_ROOT))
)
def test_core_module_is_pure(path: pathlib.Path) -> None:
    tree = ast.parse(path.read_text())
    modules = _imported_modules(tree, _package_parts(path))
    forbidden = sorted({m for m in modules if _is_forbidden(m)})
    assert not forbidden, (
        f"{path.relative_to(CORE_ROOT)} imports forbidden modules: {forbidden}"
    )
