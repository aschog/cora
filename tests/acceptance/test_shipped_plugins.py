"""Every plugin cora ships, through the loader that will really load it.

Here rather than in a plugin's own suite, which asserts what the plugin registers and
needs no loader to do it. Whether a module loads at all is its own subject, and it is
the same question for every plugin — asking it once, over the modules found in the
namespace, covers the next plugin as well as these two.
"""

import importlib
import pathlib
import pkgutil

import pytest

import cora.plugins
from app_builder import assembled, indexed
from cora.engine.plugin_registry import load_plugin, load_plugins
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME
from cora.plugins.travel import CORPUS
from cora.ports.chat_model import ModelReply
from cora.ports.host import Extension
from cora.ports.plugin import ToolCall
from fakes import ScriptedChatModel


def _shipped_modules() -> list[str]:
    """Found through the namespace rather than the manifests: `cora.plugins` spans every
    plugin installed, and asking it covers them all without knowing which distribution
    each arrived from."""
    return sorted(
        f"cora.plugins.{found.name}"
        for found in pkgutil.iter_modules(cora.plugins.__path__)
    )


def test_the_shipped_plugins_are_discovered() -> None:
    """Parametrising over an empty discovery skips rather than fails, so the walk is
    asserted on separately: no module found is a broken walk, not a clean workspace."""
    assert _shipped_modules()


@pytest.mark.parametrize("module", _shipped_modules())
def test_a_shipped_plugin_loads_through_the_registry(module: str) -> None:
    loaded = load_plugin(module)

    assert isinstance(loaded, Extension)
    assert loaded.module == module


@pytest.mark.parametrize("module", _shipped_modules())
def test_a_shipped_plugin_also_loads_as_a_drop_in(
    module: str, tmp_path: pathlib.Path
) -> None:
    """Shipped in the monorepo, written independent: each package must load through
    the folder too, exactly as a deployment that never installed it would load it."""
    package = pathlib.Path(importlib.import_module(module).__file__ or "").parent
    (tmp_path / package.name).symlink_to(package)

    (loaded,) = load_plugins([], folder=tmp_path)

    assert loaded.module == package.name


@pytest.mark.parametrize("module", _shipped_modules())
def test_a_shipped_plugin_imports_its_own_siblings_relatively(module: str) -> None:
    """The load test above cannot catch an absolute self-import here, because the
    editable install resolves it to the same files — on a machine where the package is
    only dropped, it resolves to nothing. The source is what has to say `from .`."""
    package = pathlib.Path(importlib.import_module(module).__file__ or "").parent
    offenders = [
        f"{found.name}:{number}: {line.strip()}"
        for found in sorted(package.glob("*.py"))
        for number, line in enumerate(found.read_text().splitlines(), start=1)
        if f"from {module}" in line or f"import {module}" in line
    ]

    assert not offenders, (
        "an absolute self-import breaks the package as a drop-in; write `from .`:\n"
        + "\n".join(offenders)
    )


TRIP = "How early should I book a sleeper?"


@pytest.mark.integration
def test_the_travel_corpus_is_cora_s_to_search_once_it_is_uploaded() -> None:
    """The field routing routes to has to have something in it. The notes ship as files
    and are ingested like any upload, so what answers a travel question is the plugin's
    own material — cited, and openable back to the passage."""
    app = indexed(
        assembled(
            chat_model=ScriptedChatModel(
                [
                    ModelReply(
                        tool_calls=(
                            ToolCall(
                                name=SEARCH_TOOL_NAME,
                                arguments={"query": "sleeper booking"},
                                call_id="c1",
                            ),
                        )
                    ),
                    ModelReply(text="Book it weeks ahead [1]."),
                ]
            ),
            plugins=(load_plugin("cora.plugins.travel"),),
            scopes=("travel",),
        ),
        *((path.name, path.read_bytes()) for path in sorted(CORPUS.glob("*.md"))),
        scope="travel",
    )

    answered = app.agent.answer(TRIP, "t1")

    shipped = {path.name for path in CORPUS.glob("*.md")}
    assert answered.answer == "Book it weeks ahead [1]."
    assert {citation.document for citation in answered.citations} <= shipped
    assert answered.citations, "the answer rests on the plugin's own notes"
