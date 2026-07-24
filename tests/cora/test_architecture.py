"""Architecture fitness test: `cora.core` is a pure, framework-free center.

Walks every module under `cora.core` (AST, no import side effects) and asserts it
imports neither a volatile framework nor anything from the outer layers
(`adapters`, `plugins`, `app`). This makes the §3 dependency rule automatic
instead of review-only.
"""

import ast
import pathlib

import pytest

import cora.core

# The volatile frameworks the architecture confines to a single adapter each
# (webapp-overview.md §2, §5). pypdf and jsonschema are lightweight utilities
# the core services use directly and are intentionally not listed here.
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
CORE_FILES = sorted(CORE_ROOT.rglob("*.py"))


def _imported_modules(tree: ast.Module):
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            yield node.module


def _is_forbidden(module: str) -> bool:
    if module.split(".")[0] in FORBIDDEN_FRAMEWORKS:
        return True
    return any(
        module == layer or module.startswith(f"{layer}.") for layer in FORBIDDEN_LAYERS
    )


def test_core_modules_discovered() -> None:
    assert CORE_FILES, "no cora.core modules discovered — walker is misconfigured"


@pytest.mark.parametrize(
    "path", CORE_FILES, ids=lambda p: str(p.relative_to(CORE_ROOT))
)
def test_core_module_is_pure(path: pathlib.Path) -> None:
    tree = ast.parse(path.read_text())
    forbidden = sorted({m for m in _imported_modules(tree) if _is_forbidden(m)})
    assert not forbidden, (
        f"{path.relative_to(CORE_ROOT)} imports forbidden modules: {forbidden}"
    )
