"""The architecture rules ruff cannot state.

The layer boundaries — who may import whom — are a deny-list, and a `.ruff.toml` per
layer holds them, enforced on every file by having been put in that directory. What is
left here are the other three shapes: an allow-list, which no lint rule expresses, a
rule about the words a file uses rather than the modules it imports, and the half of
the docstring policy `pydocstyle` has no rule for — a private name carries no docstring,
neither does a constant, a variable or a type alias, and no docstring runs past twelve
lines of prose.
"""

import ast
import dataclasses
import inspect
import itertools
import pathlib
import pkgutil
import re
import subprocess
import sys
import typing
from types import ModuleType

import pytest

import cora.adapters
import cora.app
import cora.domain
import cora.engine
import cora.frontends
import cora.plugins
import cora.ports
import sequences
import workspace
from app_builder import assembled
from cora.adapters.langgraph_runner import GATE
from cora.app.assembly import App
from cora.engine.steps import GateStep, ToolStep
from cora.engine.tool_runtime import ToolRuntime
from cora.ports.graph import TOOLS
from fixture_plugins import make_plugin

PURE_MAY_USE = frozenset({"jsonschema"})

# Every technology each portion of an extension point may import, and nothing outside
# it. Keyed by portion rather than by layer: one set across a layer would read as "a
# frontend may import whatever any frontend imports", which is how a widget shell
# quietly grows an HTTP server.
TOOLKITS: dict[str, frozenset[str]] = {
    "react": frozenset({"starlette", "uvicorn", "python_multipart"}),
    "fitness": frozenset(),
    "security": frozenset(),
    "travel": frozenset({"httpx"}),
}


def _root(module: ModuleType) -> pathlib.Path:
    return pathlib.Path(str(module.__file__)).parent


PURE_ROOTS = (_root(cora.domain), _root(cora.ports), _root(cora.engine))
CORE_FILES = sorted(file for root in PURE_ROOTS for file in root.rglob("*.py"))
EXTENSION_FILES = sorted(
    file
    for point in (cora.plugins, cora.frontends)
    for portion in point.__path__
    for file in pathlib.Path(portion).rglob("*.py")
)
SHIPPED = workspace.ROOT / "src" / "cora"


def _shipped_as(path: pathlib.Path) -> pathlib.Path:
    src = next(parent for parent in path.parents if parent.name == "src")
    return path.relative_to(src)


def _imported_roots(path: pathlib.Path) -> set[str]:
    tree = ast.parse(path.read_text())
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def _is_technology(root: str) -> bool:
    return root != "cora" and root not in sys.stdlib_module_names


@pytest.mark.parametrize("path", CORE_FILES, ids=lambda p: str(_shipped_as(p)))
def test_the_contract_and_the_engine_bind_no_technology(path: pathlib.Path) -> None:
    bound = sorted(
        root
        for root in _imported_roots(path)
        if _is_technology(root) and root not in PURE_MAY_USE
    )

    assert not bound, f"{_shipped_as(path)} binds {bound}"


@pytest.mark.parametrize("path", EXTENSION_FILES, ids=lambda p: str(_shipped_as(p)))
def test_an_extension_binds_only_the_technology_its_own_portion_was_given(
    path: pathlib.Path,
) -> None:
    portion = _shipped_as(path).parts[2]
    allowed = TOOLKITS[portion]

    bound = sorted(
        root
        for root in _imported_roots(path)
        if _is_technology(root) and root not in allowed
    )

    assert not bound, (
        f"{_shipped_as(path)} reaches for {bound}, which '{portion}' was not given"
    )


def _names(source: str) -> set[str]:
    tree = ast.parse(source)
    prose = {
        id(node.body[0].value)
        for node in (tree, *ast.walk(tree))
        if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef)
        and node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and isinstance(node.body[0].value.value, str)
    }
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            found.add(node.id)
        elif isinstance(node, ast.Attribute):
            found.add(node.attr)
        elif isinstance(node, ast.arg):
            found.add(node.arg)
        elif isinstance(node, ast.FunctionDef | ast.ClassDef):
            found.add(node.name)
        elif (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in prose
        ):
            found.update(re.findall(r"\w+", node.value))
    for quoted in re.findall(r"`([^`\n]+)`", source):
        found.update(re.findall(r"\w+", quoted))
    return {word.lower() for word in found}


def _shipped_scopes() -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                scope
                for module in pkgutil.iter_modules(cora.plugins.__path__)
                if (scope := getattr(_loaded(module.name), "SCOPE", None))
            }
        )
    )


def _loaded(name: str) -> ModuleType:
    import importlib

    return importlib.import_module(f"cora.plugins.{name}")


DOMAIN_WORDS = ("fitness", *_shipped_scopes())


@pytest.mark.parametrize("word", DOMAIN_WORDS)
def test_nothing_shipped_names_a_plugin_or_the_field_it_registers(word: str) -> None:
    """A field is a plugin's word, not cora's: naming one under `src/cora/` would be the
    core knowing what it is for, which is the claim the whole contract rests on.

    A name rather than a word, so a docstring explaining the settings namespace with
    `fitness` in it is the core knowing a plugin, and "passages travel in a message" is
    not the travel field.
    """
    listed = subprocess.run(
        ["git", "ls-files", "-z", "--", "src/cora/*.py"],
        capture_output=True,
        check=True,
        cwd=workspace.ROOT,
        text=True,
    )
    named = sorted(
        name
        for name in listed.stdout.split("\0")
        if name and word in _names((workspace.ROOT / name).read_text())
    )

    assert named == [], "\n".join([f"these name '{word}':", *named])


def _domain_classes() -> list[type]:
    return sorted(
        {
            kind
            for module in pkgutil.iter_modules(cora.domain.__path__)
            for _, kind in inspect.getmembers(
                _domain_module(module.name), inspect.isclass
            )
            if kind.__module__.startswith("cora.domain")
            and not kind.__name__.startswith("_")
            and not issubclass(kind, Exception)
        },
        key=lambda kind: f"{kind.__module__}.{kind.__name__}",
    )


def _domain_module(name: str) -> ModuleType:
    import importlib

    return importlib.import_module(f"cora.domain.{name}")


def _states_a_shape(kind: type) -> bool:
    return (
        inspect.isabstract(kind)
        or typing.is_typeddict(kind)
        or issubclass(kind, BaseException)
        or bool(getattr(kind, "_is_protocol", False))
    )


@pytest.mark.parametrize(
    "kind", _domain_classes(), ids=lambda kind: f"{kind.__module__}.{kind.__name__}"
)
def test_a_value_in_the_domain_is_a_frozen_dataclass(kind: type) -> None:
    """One shape for a value, so it is read by name and cannot be mistaken for what it
    is made of. A `NamedTuple` also unpacks, indexes and compares equal to a plain tuple
    of the same fields — three readings of a value the domain never means.
    """
    params = getattr(kind, "__dataclass_params__", None)
    frozen = dataclasses.is_dataclass(kind) and bool(params and params.frozen)

    named = f"{kind.__module__}.{kind.__name__}"

    assert frozen or _states_a_shape(kind), (
        f"{named} carries data without being a frozen dataclass"
    )


def test_no_path_reaches_the_tools_without_passing_the_gate() -> None:
    """The gate is unbypassable by construction rather than by discipline, and this is
    what reads that off the wiring: the round's route arrives at it, the ask's leads
    into it, and nothing else leads to the tools at all.

    Read as a shape rather than as behaviour, because behaviour catches the wrong break.
    A gate swapped out for something else fails every test that watches a turn; a
    *second* edge into the tools beside the gated one fails none of them, and that is
    the change that would get an effect through without asking anyone.
    """
    plan = sequences.routing()

    assert [here for here, there in plan.edges if there == TOOLS] == [GATE]
    assert [route for route, target in plan.routes if target == TOOLS] == [], (
        "the router sends a round to the gate; it has no route to the tools"
    )
    assert plan.after(GATE) == TOOLS


def test_the_gate_and_the_runtime_are_offered_the_same_tools() -> None:
    """The guard above proves no call reaches a tool without passing the gate. That
    only means something while the gate and the runtime are looking at the same
    tools: one offered a tool the other had never heard of would run it ungated, and
    every other test in the suite would still pass.
    """
    app = assembled(plugin=make_plugin(scope="somewhere"))
    gate, runtime = _gate_and_runtime(app)

    assert _offered(gate, frozenset({"somewhere"})) == _offered(
        runtime, frozenset({"somewhere"})
    )
    assert _offered(gate, frozenset()) == _offered(runtime, frozenset())


def _gate_and_runtime(app: App) -> tuple[GateStep, ToolRuntime]:
    loop = app.agent.runner.loop  # ty: ignore[unresolved-attribute]
    tools = loop.tools
    assert isinstance(loop.gate, GateStep) and isinstance(tools, ToolStep)
    assert isinstance(tools.tool_runtime, ToolRuntime)
    return loop.gate, tools.tool_runtime


def _offered(part: GateStep | ToolRuntime, scopes: frozenset[str]) -> set[str]:
    return {tool.name for tool in (*part.tools, *part.registry.tools(scopes))}


# Every directory whose files a layer rule speaks for. The bans themselves are ruff's —
# one `.ruff.toml` per layer, applied by a file having been put there — and this is the
# rule that the *file* exists: ruff's config is hierarchical and does not merge, so a
# layer added without one inherits the root and is silently unbanned from everything.
LAYER_DIRS = (
    *PURE_ROOTS,
    _root(cora.adapters),
    _root(cora.app),
    # A portion of an extension point, not the namespace over them: `cora.plugins` is
    # one name across as many trees as there are plugins installed, and it is the
    # plugin's own directory that its files sit under.
    *sorted({file.parent for file in EXTENSION_FILES}),
)


@pytest.mark.parametrize(
    "layer", LAYER_DIRS, ids=lambda path: str(_shipped_as(path / "x").parent)
)
def test_every_layer_says_in_its_own_directory_what_it_may_not_reach_for(
    layer: pathlib.Path,
) -> None:
    assert (layer / ".ruff.toml").is_file(), (
        f"{layer} has no .ruff.toml, so ruff bans it from nothing"
    )


def _tracked_python() -> list[pathlib.Path]:
    listed = subprocess.run(
        ["git", "ls-files", "-z", "--", "*.py"],
        capture_output=True,
        check=True,
        cwd=workspace.ROOT,
        text=True,
    )
    return [workspace.ROOT / name for name in listed.stdout.split("\0") if name]


def _documented_privates(path: pathlib.Path) -> list[str]:
    return sorted(
        node.name
        for node in ast.walk(ast.parse(path.read_text()))
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        and node.name.startswith("_")
        and not (node.name.startswith("__") and node.name.endswith("__"))
        and ast.get_docstring(node)
    )


def test_no_private_name_carries_a_docstring() -> None:
    """A docstring is written for a reader who cannot see the body, and a private name
    has no such reader: no page renders one and nothing outside the module may call it.
    What a helper is for belongs in its name, and what its body does is the body's.
    """
    documented = sorted(
        f"{path.relative_to(workspace.ROOT)}: {private}"
        for path in _tracked_python()
        for private in _documented_privates(path)
    )

    assert documented == [], "\n".join(
        ["these are private and documented:", *documented]
    )


MAX_PROSE_LINES = 12
SECTION = re.compile(r"^(Args|Returns|Yields|Raises|Attributes|Examples?|Notes?):$")


def _prose(docstring: str) -> list[str]:
    lines = docstring.splitlines()
    sectioned = (index for index, line in enumerate(lines) if SECTION.match(line))
    return lines[: next(sectioned, len(lines))]


def _long_docstrings(path: pathlib.Path) -> list[tuple[str, int]]:
    documented = (
        (node.name, ast.get_docstring(node))
        for node in ast.walk(ast.parse(path.read_text()))
        if isinstance(node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef)
    )
    return [
        (name, len(_prose(docstring)))
        for name, docstring in documented
        if docstring and len(_prose(docstring)) > MAX_PROSE_LINES
    ]


def test_no_docstring_runs_past_twelve_lines_of_prose() -> None:
    """A docstring is read beside the signature, not instead of it, and one that fills
    a screen is a page written in the wrong file: past this much there is a flow being
    retold, and `docs/big-picture.md` and `docs/happy-path.md` are where a flow lives.

    The prose, not the whole: a Google section is a table keyed to the signature, and
    `assemble` takes eighteen arguments. A module is not counted either — it has no
    signature to be read beside, and a file's opening is the one place a page belongs.
    """
    long = sorted(
        f"{path.relative_to(workspace.ROOT)}: {name} ({lines} lines)"
        for path in _tracked_python()
        for name, lines in _long_docstrings(path)
    )

    assert long == [], "\n".join(
        [f"these run past {MAX_PROSE_LINES} lines of prose:", *long]
    )


def _documented_assignments(path: pathlib.Path) -> list[str]:
    documented = []
    for node in ast.walk(ast.parse(path.read_text())):
        body = getattr(node, "body", None)
        if not isinstance(body, list) or isinstance(
            node, ast.FunctionDef | ast.AsyncFunctionDef
        ):
            continue
        for assigned, following in itertools.pairwise(body):
            if not isinstance(assigned, ast.Assign | ast.AnnAssign):
                continue
            if isinstance(following, ast.Expr) and isinstance(
                following.value, ast.Constant | ast.JoinedStr
            ):
                target = (
                    assigned.targets[0]
                    if isinstance(assigned, ast.Assign)
                    else assigned.target
                )
                documented.append(ast.unparse(target))
    return documented


def test_no_assignment_carries_a_docstring() -> None:
    """A constant, a variable and a type alias say what they are by being named: the
    string a reader wants is the value on the line above, and a paragraph under it is
    prose that drifts out of sync with a value nobody has to reread it to change.
    A page belongs in `docs/`, a reason belongs in the commit, and neither is an
    attribute docstring.
    """
    documented = sorted(
        f"{path.relative_to(workspace.ROOT)}: {name}"
        for path in _tracked_python()
        for name in _documented_assignments(path)
    )

    assert documented == [], "\n".join(
        ["these are assigned and documented:", *documented]
    )
