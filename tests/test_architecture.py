import ast
import pathlib
from types import ModuleType

import pytest

import cora.adapters
import cora.app
import cora.domain
import cora.engine
import cora.frontends.streamlit
import cora.plugins.fitness
import cora.ports

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
TEST_ONLY_FRAMEWORKS = frozenset({"pytest"})


def _root(module: ModuleType) -> pathlib.Path:
    return pathlib.Path(str(module.__file__)).parent


# Every shipped layer, each asked of its module rather than of a directory: since the
# split there is no single tree holding all of cora, and a walker rooted at one package
# passes while silently covering none of the others. The contract now ships apart from
# the engine, so the pure set spans two distributions and three modules.
PURE_ROOTS = (_root(cora.domain), _root(cora.ports), _root(cora.engine))
LAYER_ROOTS = (
    *PURE_ROOTS,
    _root(cora.adapters),
    _root(cora.app),
    _root(cora.plugins.fitness).parent,
    _root(cora.frontends.streamlit).parent,
)
CORE_FILES = sorted(file for root in PURE_ROOTS for file in root.rglob("*.py"))
PACKAGE_FILES = sorted(file for root in LAYER_ROOTS for file in root.rglob("*.py"))
UI_ROOT = _root(cora.frontends.streamlit)

# What each layer may not reach for, and the reason it may not. One table rather than a
# test per layer: a rule added here is enforced over every file of that layer, and the
# reason travels into the failure message instead of a docstring nobody reads on the way
# to fixing it.
OUT_OF_REACH: dict[str, tuple[tuple[str, ...], str]] = {
    "the contract and the engine": (
        ("cora.adapters", "cora.plugins", "cora.app", "cora.frontends"),
        "the use cases and the slots they drive are what every outer layer depends on, "
        "so they may depend on none of them",
    ),
    "the adapters": (
        ("cora.engine", "cora.app", "cora.frontends"),
        "an adapter fills a slot and is reusable by every frontend and every "
        "version of the use cases, which it can only be if it knows the ports alone",
    ),
    "the app": (
        ("cora.frontends",),
        "the composition root is what a frontend installs, so naming one would mean a "
        "command-line shell had to install a web UI to reuse the wiring",
    ),
}
LAYER_FILES: dict[str, list[pathlib.Path]] = {
    "the contract and the engine": CORE_FILES,
    "the adapters": sorted(_root(cora.adapters).rglob("*.py")),
    "the app": sorted(_root(cora.app).rglob("*.py")),
}
REACH_CASES = [(layer, path) for layer, files in LAYER_FILES.items() for path in files]


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
    """A framework, or a layer the contract and the engine may not reach for."""
    if module.split(".")[0] in FORBIDDEN_FRAMEWORKS:
        return True
    return bool(_reaches_any(module, OUT_OF_REACH["the contract and the engine"][0]))


def _reaches_any(module: str, layers: tuple[str, ...]) -> bool:
    return any(module == layer or module.startswith(f"{layer}.") for layer in layers)


def test_the_pure_modules_are_discovered() -> None:
    assert len(PURE_ROOTS) == 3, "the contract and the engine span three modules"
    assert CORE_FILES, "no pure modules discovered — the walker is misconfigured"


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
        f"{_shipped_as(path)} imports streamlit outside cora/frontends/streamlit"
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


def _reaches(
    tree: ast.Module, package_parts: tuple[str, ...], layers: tuple[str, ...]
) -> list[str]:
    modules = _imported_modules(tree, package_parts)
    return sorted({module for module in modules if _reaches_any(module, layers)})


def test_a_layer_reaching_outward_is_detected() -> None:
    tree = ast.parse("from cora.engine.steps import Router\n")
    layers, _ = OUT_OF_REACH["the adapters"]
    assert _reaches(tree, ("cora", "adapters"), layers) == ["cora.engine.steps"]


def test_every_layer_with_a_rule_has_files_to_apply_it_to() -> None:
    assert OUT_OF_REACH.keys() == LAYER_FILES.keys()
    assert all(LAYER_FILES[layer] for layer in OUT_OF_REACH)


@pytest.mark.parametrize(
    ("layer", "path"),
    REACH_CASES,
    ids=lambda value: (
        str(_shipped_as(value))
        if isinstance(value, pathlib.Path)
        else value.replace(" ", "-")
    ),
)
def test_a_layer_reaches_no_further_than_its_rule(
    layer: str, path: pathlib.Path
) -> None:
    layers, because = OUT_OF_REACH[layer]
    reached = _reaches(ast.parse(path.read_text()), _package_parts(path), layers)
    assert not reached, f"{_shipped_as(path)} reaches {reached}: {because}"
