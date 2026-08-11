import ast
import pathlib
from types import ModuleType

import pytest

import cora.adapters
import cora.app
import cora.core
import cora.plugins.fitness

FORBIDDEN_FRAMEWORKS = frozenset(
    {
        "langchain",
        "langchain_openai",
        "langchain_core",
        "chromadb",
        "langgraph",
        "sentence_transformers",
        "streamlit",
        "rank_bm25",
    }
)
FORBIDDEN_LAYERS = ("cora.adapters", "cora.plugins", "cora.app")
TEST_ONLY_FRAMEWORKS = frozenset({"pytest"})
SERVICE_LAYER = "cora.core.service_layer"


def _root(module: ModuleType) -> pathlib.Path:
    return pathlib.Path(str(module.__file__)).parent


# Every shipped layer, each from its own distribution. Asked of the modules rather
# than of one directory: since the split there is no single tree holding all of
# cora, and a walker rooted at one package would pass by silently missing the rest.
CORE_ROOT = _root(cora.core)
LAYER_ROOTS = (
    CORE_ROOT,
    _root(cora.adapters),
    _root(cora.app),
    _root(cora.plugins.fitness).parent,
)
CORE_FILES = sorted(CORE_ROOT.rglob("*.py"))
DOMAIN_ROOT = CORE_ROOT / "domain"
PACKAGE_FILES = sorted(file for root in LAYER_ROOTS for file in root.rglob("*.py"))
UI_ROOT = _root(cora.app) / "entrypoints"


def _shipped_as(path: pathlib.Path) -> pathlib.Path:
    """The module path a file ships under — `cora/core/chunk.py` — which is the same
    whichever distribution carries it."""
    src = next(parent for parent in path.parents if parent.name == "src")
    return path.relative_to(src)


def _package_parts(path: pathlib.Path) -> tuple[str, ...]:
    parts = _shipped_as(path).with_suffix("").parts
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


def _test_only_imports(path: pathlib.Path) -> list[str]:
    tree = ast.parse(path.read_text())
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.split(".")[0])
    return sorted(roots & TEST_ONLY_FRAMEWORKS)


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
    ids=lambda p: str(_shipped_as(p)),
)
def test_streamlit_stays_inside_the_ui_shell(path: pathlib.Path) -> None:
    assert not _imports_streamlit(path), (
        f"{_shipped_as(path)} imports streamlit outside cora/app/entrypoints"
    )


def test_test_only_import_is_detected(tmp_path: pathlib.Path) -> None:
    rogue = tmp_path / "rogue.py"
    rogue.write_text("from pytest import fixture\n")
    assert _test_only_imports(rogue) == ["pytest"]

    innocent = tmp_path / "innocent.py"
    innocent.write_text("import json\n")
    assert _test_only_imports(innocent) == []


@pytest.mark.parametrize("path", PACKAGE_FILES, ids=lambda p: str(_shipped_as(p)))
def test_no_test_only_framework_is_shipped(path: pathlib.Path) -> None:
    leaked = _test_only_imports(path)
    assert not leaked, f"{_shipped_as(path)} imports test-only frameworks: {leaked}"


def test_rank_bm25_import_into_core_is_detected() -> None:
    tree = ast.parse("import rank_bm25\n")
    modules = set(_imported_modules(tree, ("cora", "core", "services")))
    assert any(_is_forbidden(m) for m in modules)


def test_langgraph_import_into_core_is_detected() -> None:
    tree = ast.parse("from langgraph.graph import StateGraph\n")
    modules = set(_imported_modules(tree, ("cora", "core", "services")))
    assert any(_is_forbidden(m) for m in modules)


def test_relative_import_into_outer_layer_is_detected() -> None:
    tree = ast.parse("from ...adapters import chroma_retriever\n")
    pkg = ("cora", "core", "services")
    modules = set(_imported_modules(tree, pkg))
    assert "cora.adapters" in modules
    assert any(_is_forbidden(m) for m in modules)


@pytest.mark.parametrize("path", CORE_FILES, ids=lambda p: str(_shipped_as(p)))
def test_core_module_is_pure(path: pathlib.Path) -> None:
    tree = ast.parse(path.read_text())
    modules = _imported_modules(tree, _package_parts(path))
    forbidden = sorted({m for m in modules if _is_forbidden(m)})
    assert not forbidden, f"{_shipped_as(path)} imports forbidden modules: {forbidden}"


def _service_layer_imports(
    tree: ast.Module, package_parts: tuple[str, ...]
) -> list[str]:
    modules = _imported_modules(tree, package_parts)
    return sorted(
        {m for m in modules if m == SERVICE_LAYER or m.startswith(f"{SERVICE_LAYER}.")}
    )


def test_a_service_layer_import_into_the_domain_is_detected() -> None:
    tree = ast.parse(f"from {SERVICE_LAYER}.knowledge_base import KnowledgeBase\n")
    assert _service_layer_imports(tree, ("cora", "core", "domain")) == [
        f"{SERVICE_LAYER}.knowledge_base"
    ]


@pytest.mark.parametrize(
    "path", sorted(DOMAIN_ROOT.rglob("*.py")), ids=lambda p: str(_shipped_as(p))
)
def test_a_domain_module_does_not_import_the_service_layer(path: pathlib.Path) -> None:
    """The one boundary metadata cannot draw: domain and service layer ship in the same
    distribution, so nothing but a rule keeps the dependency running one way. Sitting in
    sibling directories makes a violation visible; this makes it fail."""
    leaked = _service_layer_imports(ast.parse(path.read_text()), _package_parts(path))
    assert not leaked, f"{_shipped_as(path)} imports the service layer: {leaked}"
