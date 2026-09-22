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
    "telegram": frozenset({"httpx"}),
    "fitness": frozenset(),
    "interview": frozenset(),
    "security": frozenset(),
    "travel": frozenset({"httpx"}),
    "vocab": frozenset(),
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


# The word the plugins mean — a training day, a drill pass — is not the core's word for
# the record a reader comes back to, so it names nothing in cora or its page.
BORROWED_WORD = "session"
SCRIPT_NOISE = re.compile(
    r'"(?:\\.|[^"\\\n])*"'
    r"|'(?:\\.|[^'\\\n])*'"
    r"|`(?:\\.|[^`\\])*`"
    r"|//[^\n]*"
    r"|/\*[\s\S]*?\*/"
)
SCRIPT_NAME = re.compile(r"[A-Za-z_$][\w$]*")
# The browser's own store is named by the browser.
PLATFORM_NAMES = frozenset({"sessionStorage"})
NAMED_IN = (
    "src/cora/*.py",
    "frontends/react/src/*.py",
    "frontends/react/ui/src/*.ts",
    "frontends/react/ui/src/*.tsx",
    ":(exclude)*.test.ts",
    ":(exclude)*.test.tsx",
    ":(exclude)frontends/react/ui/src/test/*",
)


def _script_names(source: str) -> set[str]:
    return {
        name.lower()
        for name in SCRIPT_NAME.findall(SCRIPT_NOISE.sub(" ", source))
        if name not in PLATFORM_NAMES
    }


def _named_in(path: pathlib.Path) -> set[str]:
    source = path.read_text()
    return _names(source) if path.suffix == ".py" else _script_names(source)


def test_nothing_of_cora_or_its_page_calls_a_conversation_a_session() -> None:
    listed = subprocess.run(
        ["git", "ls-files", "-z", "--", *NAMED_IN],
        capture_output=True,
        check=True,
        cwd=workspace.ROOT,
        text=True,
    )
    named = sorted(
        name
        for name in listed.stdout.split("\0")
        if name
        and any(BORROWED_WORD in found for found in _named_in(workspace.ROOT / name))
    )

    assert named == [], "\n".join([f"these name a '{BORROWED_WORD}':", *named])


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
    params = getattr(kind, "__dataclass_params__", None)
    frozen = dataclasses.is_dataclass(kind) and bool(params and params.frozen)

    named = f"{kind.__module__}.{kind.__name__}"

    assert frozen or _states_a_shape(kind), (
        f"{named} carries data without being a frozen dataclass"
    )


def test_no_path_reaches_the_tools_without_passing_the_gate() -> None:
    plan = sequences.routing()

    assert [here for here, there in plan.edges if there == TOOLS] == [GATE]
    assert [route for route, target in plan.routes if target == TOOLS] == [], (
        "the router sends a round to the gate; it has no route to the tools"
    )
    assert plan.after(GATE) == TOOLS


def test_the_gate_and_the_runtime_are_offered_the_same_tools() -> None:
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
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
        and node.name.startswith("_")
        and not (node.name.startswith("__") and node.name.endswith("__"))
        and ast.get_docstring(node)
    )


def test_no_private_name_carries_a_docstring() -> None:
    documented = sorted(
        f"{path.relative_to(workspace.ROOT)}: {private}"
        for path in _tracked_python()
        for private in _documented_privates(path)
    )

    assert documented == [], "\n".join(
        ["these are private and documented:", *documented]
    )


def _in_the_test_tree(path: pathlib.Path) -> bool:
    return "tests" in path.parts or path.name == "conftest.py"


def _documented(path: pathlib.Path) -> list[str]:
    tree = ast.parse(path.read_text())
    holders = [
        node
        for node in (tree, *ast.walk(tree))
        if isinstance(
            node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
        )
    ]
    return [
        getattr(node, "name", "<module>") for node in holders if ast.get_docstring(node)
    ]


def test_nothing_in_the_test_tree_carries_a_docstring() -> None:
    documented = sorted(
        f"{path.relative_to(workspace.ROOT)}: {name}"
        for path in _tracked_python()
        if _in_the_test_tree(path)
        for name in _documented(path)
    )

    assert documented == [], "\n".join(["these are tests and documented:", *documented])


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
    documented = sorted(
        f"{path.relative_to(workspace.ROOT)}: {name}"
        for path in _tracked_python()
        for name in _documented_assignments(path)
    )

    assert documented == [], "\n".join(
        ["these are assigned and documented:", *documented]
    )
