import ast
import pathlib
import re
from types import ModuleType

import pytest

import cora.adapters
import cora.app
import cora.domain
import cora.engine
import cora.frontends.streamlit
import cora.plugins
import cora.ports
import workspace

PURE_MAY_USE = frozenset({"jsonschema"})
"""The one declared dependency the contract and the engine may reach for. Validating a
tool's schema is a rule about what a plugin declares, not a technology the engine is
bound to — a deployment cannot swap it for a different one."""
REACHED_THROUGH = frozenset({"langchain", "langchain_core"})
"""Frameworks no manifest names but every environment holds: `langchain-openai` brings
them, and importing either binds a layer exactly as tightly as importing what declared
them."""


def _declared_technologies() -> frozenset[str]:
    """Every third party any member declares, as the name an import would use. Read off
    the manifests rather than listed, so `uv add` cannot leave the guard stale: a
    dependency added tomorrow is out of the pure layers' reach the same day, and putting
    it *in* reach means saying so in `PURE_MAY_USE`."""
    declared = {
        re.split(r"[<>=!~\[;\s]", requirement)[0]
        for member in workspace.members()
        for requirement in workspace.manifest(member)["project"]["dependencies"]
    }
    return frozenset(
        name.replace("-", "_") for name in declared if not name.startswith("cora")
    )


FORBIDDEN_FRAMEWORKS = (_declared_technologies() | REACHED_THROUGH) - PURE_MAY_USE
TEST_ONLY_FRAMEWORKS = frozenset({"pytest"})


def test_a_declared_technology_cannot_be_left_off_the_guard() -> None:
    """Which formats a deployment reads is the adapters' business, so `pypdf` is out of
    the engine's reach — and it is there because the manifest names it, not because
    someone remembered to add it here."""
    assert "pypdf" in FORBIDDEN_FRAMEWORKS


def test_the_guard_covers_every_technology_the_workspace_ships() -> None:
    """The derivation asserted against, so a walk that discovered nothing cannot pass by
    forbidding nothing. `jsonschema` is the deliberate exception and stays out."""
    assert {
        "chromadb",
        "langgraph",
        "sentence_transformers",
        "streamlit",
        "pypdf",
    } <= FORBIDDEN_FRAMEWORKS
    assert not FORBIDDEN_FRAMEWORKS & PURE_MAY_USE


def _root(module: ModuleType) -> pathlib.Path:
    return pathlib.Path(str(module.__file__)).parent


# Every shipped layer, each asked of its module rather than of a directory: the layers
# are siblings under one `src/cora/`, and a rule that named the directory would have to
# be rewritten the day a layer ships from somewhere else — which is what `cora.plugins`
# already does.
PURE_ROOTS = (_root(cora.domain), _root(cora.ports), _root(cora.engine))
EXTENSION_POINTS = (cora.plugins, cora.frontends)
"""The two namespaces that expect contributors. Asked of the namespace rather than of a
directory: `cora.plugins` is one name over as many trees as there are plugins installed,
and a walk rooted at any one of them passes by covering none of the others."""


def _extension_roots() -> tuple[pathlib.Path, ...]:
    """Every portion of an extension point. A namespace package carries one `__path__`
    entry per distribution contributing to it, so a plugin added later is walked without
    being listed here."""
    return tuple(
        sorted(
            pathlib.Path(portion)
            for point in EXTENSION_POINTS
            for portion in point.__path__
        )
    )


LAYER_ROOTS = (
    *PURE_ROOTS,
    _root(cora.adapters),
    _root(cora.app),
    *_extension_roots(),
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
        ("cora.frontends", "cora.plugins"),
        "the composition root is what a frontend installs, so naming a frontend would "
        "mean a command-line shell had to install a web UI to reuse the wiring; and it "
        "installs no plugin at all, which is why importing one rather than naming "
        "it in config has to stay impossible",
    ),
    "the plugins": (
        ("cora.engine", "cora.adapters", "cora.app", "cora.frontends"),
        "a plugin is data over the contract, which is what lets it ship as a wheel "
        "the engine is absent from: reaching any of these makes it a plugin only this "
        "deployment can install",
    ),
    "the frontends": (
        ("cora.adapters", "cora.plugins"),
        "a frontend shows what the app and the use cases hand it; reaching an adapter "
        "ties the UI to one technology binding, and naming a plugin ties it to one "
        "domain — both are chosen at assembly, not at the screen",
    ),
}
PLUGIN_ROOTS = tuple(root for root in _extension_roots() if root.name == "plugins")
FRONTEND_ROOTS = tuple(root for root in _extension_roots() if root.name == "frontends")
LAYER_FILES: dict[str, list[pathlib.Path]] = {
    "the contract and the engine": CORE_FILES,
    "the adapters": sorted(_root(cora.adapters).rglob("*.py")),
    "the app": sorted(_root(cora.app).rglob("*.py")),
    "the plugins": sorted(file for root in PLUGIN_ROOTS for file in root.rglob("*.py")),
    "the frontends": sorted(
        file for root in FRONTEND_ROOTS for file in root.rglob("*.py")
    ),
}
REACH_CASES = [(layer, path) for layer, files in LAYER_FILES.items() for path in files]


def _shipped_as(path: pathlib.Path) -> pathlib.Path:
    """The module path a file ships under — `cora/domain/chunk.py` — which is the same
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


@pytest.mark.parametrize(
    "path",
    [p for p in PACKAGE_FILES if not p.is_relative_to(UI_ROOT)],
    ids=lambda p: str(_shipped_as(p)),
)
def test_streamlit_stays_inside_the_ui_shell(path: pathlib.Path) -> None:
    assert not _imports_streamlit(path), (
        f"{_shipped_as(path)} imports streamlit outside cora/frontends/streamlit"
    )


@pytest.mark.parametrize("path", PACKAGE_FILES, ids=lambda p: str(_shipped_as(p)))
def test_no_test_only_framework_is_shipped(path: pathlib.Path) -> None:
    leaked = _test_only_imports(path)
    assert not leaked, f"{_shipped_as(path)} imports test-only frameworks: {leaked}"


@pytest.mark.parametrize("path", CORE_FILES, ids=lambda p: str(_shipped_as(p)))
def test_no_reference_domain_word_reaches_the_contract_or_the_engine(
    path: pathlib.Path,
) -> None:
    """Domain-agnostic is a claim about words as much as imports: the plugin supplies
    the topic, so the reference domain's name has no business in the layers every other
    domain reuses. `cora.app.config` names it as the default plugin and is allowed to —
    which domain a deployment ships is its choice, not the engine's."""
    assert "fitness" not in path.read_text().lower(), (
        f"{_shipped_as(path)} names the reference domain"
    )


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


def test_the_walkers_catch_a_planted_violation(tmp_path: pathlib.Path) -> None:
    """One rogue module where eight self-tests of the detectors used to be. What it
    proves is that the walks above are not vacuous: they pass by finding nothing, and a
    broken detector is indistinguishable from clean code. Those eight are also what
    rotted — three passed a `("cora", "core", "services")` package tuple naming a
    directory gone for two commits, so they could not have failed."""
    rogue = tmp_path / "rogue.py"
    rogue.write_text(
        "import streamlit as st\n"
        "import pypdf\n"
        "from langgraph.graph import StateGraph\n"
        "from pytest import fixture\n"
        "from cora.app.config import Config\n"
        "from ..adapters import chroma_retriever\n"
    )
    tree = ast.parse(rogue.read_text())

    assert _imports_streamlit(rogue)
    assert _test_only_imports(rogue) == ["pytest"]

    reached = set(_imported_modules(tree, ("cora", "engine")))
    assert "cora.adapters" in reached, (
        "a relative import out of the layer went unresolved"
    )
    assert {
        "streamlit",
        "pypdf",
        "langgraph.graph",
        "cora.app.config",
        "cora.adapters",
    } <= {module for module in reached if _is_forbidden(module)}

    outward, _ = OUT_OF_REACH["the adapters"]
    assert _reaches(tree, ("cora", "adapters"), outward) == ["cora.app.config"]


def test_the_walkers_pass_innocent_code(tmp_path: pathlib.Path) -> None:
    innocent = tmp_path / "innocent.py"
    innocent.write_text("import json\n\nfrom cora.domain.chunk import Chunk\n")
    tree = ast.parse(innocent.read_text())

    assert not _imports_streamlit(innocent)
    assert _test_only_imports(innocent) == []
    assert not [
        module
        for module in _imported_modules(tree, ("cora", "engine"))
        if _is_forbidden(module)
    ]
