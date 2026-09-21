"""The sequences the docs draw, read out of the code they are about.

A message is a call a method makes, in the order it makes them; a branch is an `alt` and
a loop a `loop`, so what comes out says what the code can do rather than what one run of
it did. Nothing here draws: `gen_session_maps.py` is what turns a `Sequence` into UML.
"""

import ast
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import gen_component_map as components
import reading

ROOT = Path(__file__).parent.parent
SRC = ROOT / "src"
FRONTENDS = ROOT / "frontends"

# What the reader cannot turn into a fragment. Drawn flat, each of these would say that
# every arm of a `match`, or one pass of a `while`, is what always happens — a fork the
# source has and the drawing denies. Better a red `make diagram` than a confident wrong
# picture, so reaching one is a failure rather than a silence.
CANNOT_DRAW = {
    ast.Match: "a match",
    ast.AsyncFor: "an async for",
    ast.AsyncWith: "an async with",
    ast.IfExp: "a conditional expression",
}


@dataclass(frozen=True)
class Lifeline:
    """One participant, as the drawing labels it: the role, and the type filling it."""

    role: str
    kind: str = ""

    @property
    def label(self) -> str:
        return f"{self.role}: {self.kind}" if self.kind else self.role


@dataclass(frozen=True)
class Call:
    """One message, from the lifeline that sends it to the lifeline that takes it."""

    sender: str
    receiver: str
    label: str


@dataclass(frozen=True)
class Reply:
    """What a call answers with, drawn back along the arrow it came in on."""

    sender: str
    receiver: str
    label: str


@dataclass(frozen=True)
class Fragment:
    """A combined fragment: the operator, and one guarded run of lines per operand."""

    operator: str
    operands: tuple[tuple[str, tuple["Line", ...]], ...]


Line = Call | Reply | Fragment


@dataclass(frozen=True)
class Sequence:
    """One drawing: who takes part, in the order they are drawn, and what passes."""

    name: str
    lifelines: tuple[Lifeline, ...]
    lines: tuple[Line, ...]


def flattened(lines: tuple[Line, ...]) -> list[Line]:
    """Every line, fragments opened out, in the order the drawing reads them."""
    out: list[Line] = []
    for line in lines:
        out.append(line)
        if isinstance(line, Fragment):
            for _, inner in line.operands:
                out.extend(flattened(inner))
    return out


def speaks(lines: tuple[Line, ...]) -> bool:
    """Whether anything is said in here. A fragment that carries no message says only
    that the code had a branch, which is what the code is for reading."""
    return any(isinstance(line, Call) for line in flattened(lines))


def _module(dotted: str) -> Path:
    return SRC.joinpath(*dotted.split(".")).with_suffix(".py")


def _klass(tree: ast.Module, name: str) -> ast.ClassDef:
    return next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == name
    )


def _method(klass: ast.ClassDef, name: str) -> ast.FunctionDef:
    return next(
        node
        for node in klass.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    )


def _head(annotation: ast.expr) -> str:
    if isinstance(annotation, ast.BinOp):
        return _head(annotation.left)
    if isinstance(annotation, ast.Subscript):
        return _head(annotation.value)
    return ast.unparse(annotation).rsplit(".", 1)[-1].strip("'\"")


def _fields(klass: ast.ClassDef) -> dict[str, str]:
    return {
        node.target.id: _head(node.annotation)
        for node in klass.body
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    }


def providers() -> dict[str, str]:
    """What fills each port, off the composition root — the component map's own reading.

    A lifeline says what is really there: `retriever: SqliteVecRetriever`, because a
    sequence is one run of the app and one run has one adapter behind each port.
    """
    return {
        binding.port: binding.providers[0]
        for binding in components.bindings()
        if len(binding.providers) == 1
    }


@dataclass(frozen=True)
class Slot:
    """One field of the class being read: the interface it is typed by, and what fills
    it. The type is where a call's signature is looked up; the provider is what the
    lifeline is labelled with, because a run has one thing behind each port.
    """

    role: str
    kind: str
    declared_in: str = ""


def _element(annotation: ast.expr) -> str:
    if isinstance(annotation, ast.Subscript):
        inner = annotation.slice
        first = inner.elts[0] if isinstance(inner, ast.Tuple) else inner
        return _head(first)
    return _head(annotation)


def _annotations(klass: ast.ClassDef) -> dict[str, ast.expr]:
    return {
        node.target.id: node.annotation
        for node in klass.body
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    }


def _returned(module: str, kind: str, method: str) -> str:
    path = _module(module)
    if not path.exists():
        return ""
    try:
        found = _method(_klass(reading.parsed(path), kind), method)
    except StopIteration:
        return ""
    return "" if found.returns is None else ast.unparse(found.returns)


def _argument(node: ast.expr) -> str:
    written = ast.unparse(node).replace("self.", "")
    return written[1:-1] if isinstance(node, ast.Tuple) else written


def _named(node: ast.expr) -> str:
    if isinstance(node, ast.Call):
        return f"{_argument(node.func).rsplit('.', 1)[-1]}(…)"
    return _argument(node)


def _label(call: ast.Call, method: str) -> str:
    written = [_named(node) for node in call.args]
    written += [
        f"{keyword.arg}={_named(keyword.value)}"
        for keyword in call.keywords
        if keyword.arg
    ]
    return f"{method}({', '.join(written)})"


ENGINE = SRC / "cora" / "engine"
ENGINE_PACKAGE = "cora.engine"


def behind() -> dict[str, str]:
    """Which class fills a port the composition root does not take as an argument.

    `ContextSource` is one: it is filled inside `assemble`, where the knowledge base is
    handed to the function that offers the tools. One hop is all it takes — the port is
    named by the annotation on the parameter it arrives on, so what stands behind it is
    the local that was passed there, and nothing has to be followed further.
    """
    tree = reading.parsed(_module(ASSEMBLY))
    root = reading.function(tree, "assemble")
    made = reading.bound(root)
    found: dict[str, str] = {}
    for call in _ordered(root):
        if not isinstance(call.func, ast.Name):
            continue
        taken = next(
            (
                node
                for node in tree.body
                if isinstance(node, ast.FunctionDef) and node.name == call.func.id
            ),
            None,
        )
        if taken is None:
            continue
        params = [*taken.args.args, *taken.args.kwonlyargs]
        paired: list[tuple[ast.arg, ast.expr]] = list(
            zip(params, call.args, strict=False)
        )
        paired += [
            (param, keyword.value)
            for keyword in call.keywords
            for param in params
            if param.arg == keyword.arg
        ]
        for param, value in paired:
            filling = made.get(value.id) if isinstance(value, ast.Name) else None
            if param.annotation is not None and filling and filling[0].isupper():
                found[_head(param.annotation)] = filling
    return found


def engine_classes() -> dict[str, str]:
    """Every class `cora.engine` declares, and the module it is declared in.

    What the drawing may open: a class of the engine is cora's own work, so its calls
    belong on the drawing. An adapter is a boundary — opening one would draw a library.
    """
    return {
        node.name: f"cora.engine.{path.stem}"
        for path in sorted(ENGINE.glob("*.py"))
        for node in reading.parsed(path).body
        if isinstance(node, ast.ClassDef)
    }


def _port_modules() -> dict[str, str]:
    return {
        node.name: f"cora.ports.{path.stem}"
        for path in sorted((SRC / "cora" / "ports").glob("*.py"))
        for node in reading.parsed(path).body
        if isinstance(node, ast.ClassDef)
    }


def wired() -> dict[tuple[str, str], str]:
    """What the composition root drops into each slot it fills by name.

    Some slots are told apart by their type and some only by their role: the tool
    runtime arrives as the `ToolExecutor` it answers for. Keyed by the class being
    constructed as well as the keyword, because a role name is not unique across the
    app — `tools` is a tuple of tools on one step and a step on the runner.

    Raises:
        SystemExit: One class is constructed twice with a keyword filled two ways, so
            what stands behind that slot depends on which call the drawing meant.
    """
    tree = reading.parsed(_module(ASSEMBLY))
    found: dict[tuple[str, str], str] = {}
    for call in _ordered(reading.function(tree, "assemble")):
        built = reading.called(call)
        if not built or not built[0].isupper():
            continue
        for keyword in call.keywords:
            filling = reading.called(keyword.value)
            if not keyword.arg or not filling or not filling[0].isupper():
                continue
            slot = (built, keyword.arg)
            if found.get(slot, filling) != filling:
                raise SystemExit(
                    f"the composition root fills {built}.{keyword.arg} with both "
                    f"{found[slot]} and {filling}: the drawing cannot say which"
                )
            found[slot] = filling
    return found


def drawn_kind(kind: str, role: str = "", inside: str = "") -> str:
    """What a slot really holds in a running app.

    By the role it is filled under where the class holding it says so, and by its type
    otherwise. `inside` is that holder: without it only the type is asked, which is what
    an object already known by its own class needs.
    """
    return (
        wired().get((inside, role)) or providers().get(kind) or behind().get(kind, kind)
    )


PORTS_PACKAGE = "cora.ports"
DOMAIN_PACKAGE = "cora.domain"


def a_participant(kind: str, where: str = "") -> bool:
    """Whether a drawing may give something a lifeline of its own.

    Anything that acts in a running app may: a class of the engine, an adapter behind a
    port, a slot typed by a port — a port names a boundary whether it is written as a
    Protocol or as a callable. `cora.domain` may not, however it arrives: the state a
    step reads and the values it makes are the vocabulary a run is written in, not
    participants in it.
    """
    if where.startswith(DOMAIN_PACKAGE):
        return False
    if where.startswith((PORTS_PACKAGE, ENGINE_PACKAGE)):
        return True
    return bool(kind) and (
        kind in engine_classes()
        or kind in _port_modules()
        or kind in set(providers().values())
        or kind == "Callable"
    )


def _guard(test: ast.expr) -> str:
    return _argument(test)


def _iterated(node: ast.expr, held: dict[str, ast.expr], scope: dict[str, str]) -> str:
    if isinstance(node, ast.Attribute) and node.attr in held:
        return _element(held[node.attr])
    if isinstance(node, ast.Name):
        return scope.get(node.id, "")
    return ""


def _refuse(node: ast.stmt, drawn: Callable[[ast.Call], object]) -> None:
    for found in ast.walk(node):
        named = CANNOT_DRAW.get(type(found))
        if named is None or not any(drawn(call) for call in _ordered(found)):
            continue
        where = getattr(found, "lineno", node.lineno)
        raise SystemExit(
            f"gen_session_maps cannot draw {named} on line {where}: it is a fork, and "
            "drawn flat every arm of it would read as unconditional. Give the reader a "
            "fragment for it, or take the calls out of it."
        )


def _caught(handler: ast.ExceptHandler) -> str:
    return "" if handler.type is None else _argument(handler.type)


def _stops(body: list[ast.stmt]) -> bool:
    return any(isinstance(node, ast.Return | ast.Raise) for node in body)


def _ordered(node: ast.AST) -> list[ast.Call]:
    found: list[ast.Call] = []
    for child in ast.iter_child_nodes(node):
        found.extend(_ordered(child))
    if isinstance(node, ast.Call):
        found.append(node)
    return found


SIGNATURE = "\x00signature"


@dataclass
class Reading:
    """The lifelines of one drawing, in the order the reading first meets them."""

    lifelines: dict[str, str]

    def met(self, role: str, kind: str = "") -> None:
        if role not in self.lifelines or (kind and not self.lifelines[role]):
            self.lifelines[role] = kind

    def drawn(self) -> tuple[Lifeline, ...]:
        return tuple(Lifeline(role, kind) for role, kind in self.lifelines.items())


def read(
    dotted: str,
    kind: str,
    method: str,
    role: str,
    met: Reading,
    seen: frozenset[tuple[str, str]] = frozenset(),
) -> tuple[Line, ...]:
    """One method as the messages it sends, in the order the body sends them.

    A branch becomes an `alt` and a loop a `loop`, so what the drawing shows is what the
    code can do rather than one run of it. A call the object makes on itself is followed
    into: a private method is the object's own work, not another participant. Following
    stops only where it would come back to a method already being read — a depth cap
    would drop whatever the last method said to anyone else, and say nothing about it.
    """
    frame = (kind, method)
    seen = seen | {frame}
    tree = reading.parsed(_module(dotted))
    klass = _klass(tree, kind)
    body = _method(klass, method)
    imported = reading.imported(tree)
    held = _annotations(klass)
    slots = {
        name: Slot(name, _head(annotation), imported.get(_head(annotation), ""))
        for name, annotation in held.items()
    }
    scope = {
        argument.arg: "" if argument.annotation is None else _head(argument.annotation)
        for argument in (*body.args.args[1:], *body.args.kwonlyargs)
    }
    met.met(role, drawn_kind(kind, role))

    def receiver_of(call: ast.Call) -> tuple[str, str] | None:
        called = call.func
        if isinstance(called, ast.Attribute):
            held = called.value
            if (
                isinstance(held, ast.Attribute)
                and isinstance(held.value, ast.Name)
                and held.value.id == "self"
                and held.attr in slots
            ):
                return held.attr, called.attr
            if isinstance(held, ast.Name):
                if held.id == "self":
                    # A slot that is called is called *on*: `self.on_text(…)` is a
                    # message to the reader, not work the step does itself.
                    return (
                        (called.attr, called.attr)
                        if called.attr in slots
                        else (
                            role,
                            called.attr,
                        )
                    )
                if held.id in scope:
                    return held.id, called.attr
            return None
        if isinstance(called, ast.Name):
            if called.id in scope:
                return called.id, called.id
            # A bare name is a participant where it is a function of the engine —
            # `ingest` does the work of a step. A class is a value being made, and
            # `cora.domain` is the vocabulary a run is written in rather than anything
            # a message is sent to.
            if imported.get(called.id, "").startswith(ENGINE_PACKAGE):
                return called.id, called.id
        return None

    def drawn(call: ast.Call) -> tuple[str, str, str] | None:
        """Who takes this call and what it is called, or nothing where it is not drawn.

        Asked twice — once to find which call of a statement answers with its value,
        once to draw it — so the answer is worked out in one place.
        """
        found = receiver_of(call)
        if found is None:
            return None
        name, message = found
        slot = slots.get(name)
        typed = slot.kind if slot else scope.get(name, "")
        stands = (
            drawn_kind(kind, role)
            if name == role
            else drawn_kind(typed, name, inside=kind)
        )
        where = slot.declared_in if slot else imported.get(name, "")
        if name != role and not a_participant(stands, where):
            return None
        return name, message, stands

    def emit(call: ast.Call, reply: str) -> list[Line]:
        found = drawn(call)
        if found is None:
            return []
        name, message, stands = found
        slot = slots.get(name)
        typed = slot.kind if slot else scope.get(name, "")
        met.met(name, stands)
        lines: list[Line] = [Call(role, name, _label(call, message))]
        answered = "" if name == role else reply
        if answered == SIGNATURE:
            answered = (
                _returned(slot.declared_in, typed, message)
                if slot and slot.declared_in
                else ""
            )
        opened = stands
        if name == role and message.startswith("_") and (kind, message) not in seen:
            lines.extend(read(dotted, kind, message, role, met, seen))
        elif (
            opened in engine_classes()
            and opened != kind
            and (opened, message) not in seen
        ):
            inside = engine_classes()[opened]
            lines.extend(read(inside, opened, message, name, met, seen))
        # After whatever the call set off, never before it: a reply closes a message.
        if answered:
            lines.append(Reply(name, role, answered))
        return lines

    def sent(node: ast.AST, reply: str) -> list[Line]:
        """Every message one statement sends, and which of them answers with its value.

        The outermost call is the one whose value the statement binds — the others are
        the arguments it was given — so the reply belongs to that one. An object does
        not answer itself, so where the outermost is a call on `self` the reply falls
        back to the outermost that is not.
        """
        calls = [call for call in _ordered(node) if drawn(call)]
        answering = next(
            (call for call in reversed(calls) if (drawn(call) or ("", ""))[0] != role),
            None,
        )
        out: list[Line] = []
        for call in calls:
            out += emit(call, reply if call is answering else "")
        return out

    def statement(node: ast.stmt) -> list[Line]:
        if isinstance(node, ast.Assign):
            return sent(node, ", ".join(_argument(one) for one in node.targets))
        if isinstance(node, ast.AnnAssign):
            return sent(node, _argument(node.target))
        if isinstance(node, ast.Return):
            return sent(node, SIGNATURE)
        return sent(node, "")

    def tested(node: ast.expr) -> list[Line]:
        return sent(node, SIGNATURE)

    def walk(statements: list[ast.stmt]) -> tuple[Line, ...]:
        out: list[Line] = []
        for index, node in enumerate(statements):
            if isinstance(node, ast.If):
                out += tested(node.test)
                taken = walk(node.body)
                if _stops(node.body):
                    # The branch leaves the method, so the rest of it is the other way
                    # out. Both go inside the fork even when one of them says nothing:
                    # a message drawn outside it would claim to happen either way, and
                    # what stands behind a guard clause is exactly what does not.
                    rest = walk([*node.orelse, *statements[index + 1 :]])
                    operands = ((_guard(node.test), taken), ("else", rest))
                    if any(speaks(inner) for _, inner in operands):
                        out.append(Fragment("alt", operands))
                    return tuple(out)
                operands = ((_guard(node.test), taken),)
                if node.orelse:
                    operands += (("else", walk(node.orelse)),)
                if any(speaks(inner) for _, inner in operands):
                    out.append(Fragment("alt", operands))
                continue
            if isinstance(node, ast.For):
                if isinstance(node.target, ast.Name):
                    scope[node.target.id] = _iterated(node.iter, held, scope)
                out += tested(node.iter)
                inner = walk(node.body)
                if speaks(inner):
                    out.append(Fragment("loop", ((_argument(node.iter), inner),)))
                continue
            if isinstance(node, ast.While):
                inner = walk(node.body)
                if speaks(inner):
                    out.append(Fragment("loop", ((_guard(node.test), inner),)))
                continue
            if isinstance(node, ast.Try):
                out += walk(node.body)
                # A handler is the path an exception takes, which is UML's `break`: the
                # rest of the fragment it stands in is abandoned. Drawn flat it would be
                # a message that arrives on every pass.
                for handler in node.handlers:
                    caught = walk(handler.body)
                    if speaks(caught):
                        out.append(Fragment("break", ((_caught(handler), caught),)))
                continue
            _refuse(node, drawn)
            out += statement(node)
        return tuple(out)

    return walk(body.body)


def _dotted(path: Path) -> str:
    parts = path.with_suffix("").parts
    return ".".join(parts[parts.index("cora") :])


def _sources() -> list[Path]:
    return [
        path
        for tree in (SRC, FRONTENDS)
        for path in sorted(tree.rglob("*.py"))
        if "tests" not in path.parts and "node_modules" not in path.parts
    ]


def callers_of(method: str, inside: str) -> str:
    """Where a call into the engine arrives from, as the package every caller shares.

    Two frontends call the same method, so what the drawing can honestly name is the
    package they have in common — the lifeline is `cora.frontends`, not one page of it.
    A named method is a call site whether it is called on the spot or handed to
    something that will call it: one frontend passes it to a thread pool.
    """
    found = {
        _dotted(path)
        for path in _sources()
        for node in _ordered(reading.parsed(path))
        for named in (node.func, *node.args)
        if isinstance(named, ast.Attribute)
        and named.attr == method
        and _dotted(path) != inside
    }
    if not found:
        raise SystemExit(f"nothing outside {inside} calls {method}")
    shared: list[str] = []
    for step in zip(*(name.split(".") for name in found), strict=False):
        if len(set(step)) > 1:
            break
        shared.append(step[0])
    return ".".join(shared)


def _signature(dotted: str, kind: str, method: str) -> str:
    body = _method(_klass(reading.parsed(_module(dotted)), kind), method)
    taken = [one.arg for one in (*body.args.args[1:], *body.args.kwonlyargs)]
    return f"{method}({', '.join(taken)})"


def _entered(
    dotted: str,
    kind: str,
    method: str,
    role: str,
    *,
    name: str = "",
    by: tuple[str, str] | None = None,
    asked: str = "",
) -> Sequence:
    met = Reading({})
    caller, kind_of = by or (callers_of(method, dotted), "")
    met.met(caller, kind_of)
    inside = read(dotted, kind, method, role, met)
    label = asked or _signature(dotted, kind, method)
    answered = _returned(dotted, kind, method)
    closing = (Reply(role, caller, answered),) if answered else ()
    return Sequence(
        name=name or role,
        lifelines=met.drawn(),
        lines=(Call(caller, role, label), *inside, *closing),
    )


def upload() -> Sequence:
    """A document going in, off `KnowledgeBase.add_file`."""
    return _entered(KNOWLEDGE, "KnowledgeBase", "add_file", "knowledge_base")


def _constant(tree: ast.Module, name: str) -> str:
    return next(
        node.value.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == name
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    )


def tool_built_in(dotted: str) -> tuple[str, str]:
    """The name the model asks for, and the class that answers to it.

    Both off the one `Tool(...)` the module builds: the drawing's own claim — that
    asking for `search_documents` runs `DocumentSearch` — is what the source says here.
    """
    tree = reading.parsed(_module(dotted))
    built = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "Tool"
    )
    keywords = {keyword.arg: keyword.value for keyword in built.keywords}
    named = keywords["name"]
    runs = keywords["run"]
    assert isinstance(named, ast.Name)
    return _constant(tree, named.id), _called_class(runs)


def _called_class(node: ast.expr) -> str:
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return node.func.id
    return _argument(node)


KNOWLEDGE = "cora.engine.knowledge_base"
RETRIEVAL = "cora.engine.retrieval_tool"


def search() -> Sequence:
    """The one tool that reaches the documents, off the class the tool is built around.

    The runtime opens it: a tool is held as a `Tool` and called through its `run` slot,
    so the class about to run is named nowhere the call is made.
    """
    named, runs = tool_built_in(RETRIEVAL)
    return _entered(
        RETRIEVAL,
        runs,
        "__call__",
        named,
        name="search",
        by=("tool_runtime", "ToolRuntime"),
        asked="run(**arguments)",
    )


ASSEMBLY = "cora.app.assembly"
RUNNER = "cora.adapters.langgraph_runner"
AGENT = "cora.engine.agent"
BUILDER = "builder"
GRAPH = "graph"


STEPS = "cora.engine.steps"


@dataclass(frozen=True)
class Walk:
    """The turn as the composition root hands it over.

    `before` and `after` are the named steps either side of the rounds, each read as the
    name it is walked under and the class that takes it. `marker` is the step the rounds
    fall inside: it says where the turn is, and `marker_kind` is what it runs there —
    `Named` where it runs nothing and leaves the round to the loop.
    """

    before: tuple[tuple[str, str], ...]
    marker: str
    marker_kind: str
    loop: dict[str, str]
    after: tuple[tuple[str, str], ...]


def _handed_over() -> ast.Call:
    tree = reading.parsed(_module(ASSEMBLY))
    return next(
        node
        for node in ast.walk(reading.function(tree, "assemble"))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == GRAPH
    )


def _named_step(node: ast.expr) -> tuple[str, str]:
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
        raise SystemExit(f"a step of the walk is not a named one: {ast.dump(node)}")
    tree = reading.parsed(_module(STEPS))
    name = _value(tree, {}, _named(node.args[0]))
    taken = reading.called(node.args[1]) if len(node.args) > 1 else ""
    return name, taken or node.func.id


def _sequence(node: ast.expr) -> tuple[tuple[str, str], ...]:
    assert isinstance(node, ast.Tuple)
    return tuple(_named_step(element) for element in node.elts)


def walked() -> Walk:
    """The walk of a turn, read off the composition root.

    The steps are named where they are wired, which is the one place that says what a
    turn is made of — the runner is handed a sequence and walks whatever is in it, so
    reading them off the runner would find a loop over a tuple and no names at all.
    """
    handed = {
        keyword.arg: keyword.value for keyword in _handed_over().keywords if keyword.arg
    }
    loop = handed["loop"]
    assert isinstance(loop, ast.Call)
    parts = {keyword.arg: keyword.value for keyword in loop.keywords if keyword.arg}
    marker, marker_kind = _named_step(parts.pop("marker"))
    return Walk(
        before=_sequence(handed["before"]),
        marker=marker,
        marker_kind=marker_kind,
        loop={
            role: kind
            for role, value in parts.items()
            if (kind := reading.called(value)) and kind[0].isupper()
        },
        after=_sequence(handed["after"]),
    )


@dataclass(frozen=True)
class Decision:
    """One conditional edge: who decides, and where each of its routes leads."""

    router: str
    routes: tuple[tuple[str, str], ...]

    def entering(self, nodes: dict[str, str]) -> str:
        """The guard under which the graph goes on: the one route that leads to a node.

        Raises:
            SystemExit: The routes lead into the graph twice, or never, so there is no
                one condition a fragment could be guarded with.
        """
        into = [route for route, target in self.routes if target in nodes]
        if len(into) != 1:
            raise SystemExit(
                f"{self.router} leads into the graph {len(into)} ways "
                f"({', '.join(into)}): a fragment is guarded by the one route that does"
            )
        return f'{self.router}(state) == "{into[0]}"'


@dataclass(frozen=True)
class Routing:
    """The graph the runner declares: what each node runs, and what leads where.

    `at`, `router` and `routes` are the loop's decision, taken at a node the runner
    names. `opening` is the decision at the marker — the one node the runner does not
    name, the composition root having named it — or nothing where it leads one way.
    """

    nodes: dict[str, str]
    edges: tuple[tuple[str, str], ...]
    at: str
    router: str
    routes: tuple[tuple[str, str], ...]
    opening: Decision | None = None

    def after(self, node: str) -> str:
        """Where one node leads, of which there is exactly one.

        Raises:
            SystemExit: A node has two unconditional edges out of it. Which one the
                drawing followed would then be arbitrary, and the other would be a path
                the page denies exists.
        """
        out = [there for here, there in self.edges if here == node]
        if len(out) > 1:
            raise SystemExit(
                f"the graph leads out of {node} to {' and '.join(out)}: a sequence can "
                "follow one, so give the reader a fragment for the choice"
            )
        return out[0] if out else ""

    @property
    def leaves(self) -> str:
        """The route that ends the turn — the one whose target is no node of the graph.

        Raises:
            SystemExit: The routes end the turn twice, or never. Either way the
                condition the loop runs under is not a thing to be read off them.
        """
        out = [route for route, target in self.routes if target not in self.nodes]
        if len(out) != 1:
            raise SystemExit(
                f"the graph's routes leave it {len(out)} ways ({', '.join(out)}): the "
                "loop's condition is the one route that does not come back"
            )
        return out[0]

    @property
    def keeps_going(self) -> str:
        """What the graph says a round is: every route but the one that leaves."""
        return f'router(state) != "{self.leaves}"'

    def chain(self, start: str) -> tuple[str, ...]:
        """The nodes one route leads through before the decision is taken again."""
        walked: list[str] = []
        node = start
        while node in self.nodes and node != self.at and node not in walked:
            walked.append(node)
            node = self.after(node)
        return tuple(walked)


def _value(tree: ast.Module, imported: dict[str, str], name: str) -> str:
    for where in (tree, *_borrowed(imported, name)):
        try:
            return _constant(where, name)
        except StopIteration:
            continue
    return name


def _borrowed(imported: dict[str, str], name: str) -> tuple[ast.Module, ...]:
    module = imported.get(name, "")
    if not module.startswith("cora."):
        return ()
    return (reading.parsed(_module(module)),)


def routing() -> Routing:
    """The graph, read off the builder the runner hands to LangGraph.

    Nodes and edges are the runner's own statements — what it says the turn's shape is —
    so the drawing takes the shape from there rather than from any run of it.
    """
    tree = reading.parsed(_module(RUNNER))
    imported = reading.imported(tree)
    body = _method(_klass(tree, "LangGraphRunner"), "_graph")
    nodes: dict[str, str] = {}
    edges: list[tuple[str, str]] = []
    at = router = ""
    routes: tuple[tuple[str, str], ...] = ()
    opening: Decision | None = None

    def named(node: ast.expr) -> str:
        return _value(tree, imported, node.id) if isinstance(node, ast.Name) else ""

    for call in _ordered(body):
        if not isinstance(call.func, ast.Attribute):
            continue
        held = call.func.value
        if not isinstance(held, ast.Name) or held.id != BUILDER:
            continue
        if call.func.attr == "add_node":
            if node := named(call.args[0]):
                nodes[node] = _role_of(call.args[1])
        elif call.func.attr == "add_edge":
            here, there = named(call.args[0]), named(call.args[1])
            if here and there:
                edges.append((here, there))
        elif call.func.attr == "add_conditional_edges":
            mapped = call.args[2]
            assert isinstance(mapped, ast.Dict)
            decided = tuple(
                (named(key), named(value))
                for key, value in zip(mapped.keys, mapped.values, strict=True)
                if key is not None
            )
            if named(call.args[0]):
                at, router, routes = (
                    named(call.args[0]),
                    _role_of(call.args[1]),
                    decided,
                )
            else:
                opening = Decision(_role_of(call.args[1]), decided)
    return Routing(nodes, tuple(edges), at, router, routes, opening)


def _role_of(node: ast.expr) -> str:
    if isinstance(node, ast.Call):
        return _role_of(node.func)
    if isinstance(node, ast.Attribute):
        return node.attr
    return _argument(node)


GRAPH_PORT = "cora.ports.graph"


def _step(
    name: str, kind: str, met: Reading, role: str, *, into: bool = True
) -> list[Line]:
    met.met(name, kind)
    lines: list[Line] = [Call(role, name, f"{name}(state)")]
    where = engine_classes().get(kind)
    if where and into:
        lines.extend(read(where, kind, "__call__", name, met))
    lines.append(Reply(name, role, _returned(GRAPH_PORT, "Step", "__call__")))
    return lines


def round_taken() -> Sequence:
    """A turn as it is walked: the steps the composition root named, and between them
    the rounds, off the nodes and edges the runner declares."""
    plan = routing()
    walk = walked()
    met = Reading({})
    role = "runner"
    met.met("agent", "Agent")
    met.met(role, providers()["GraphRunner"])

    opening: list[Line] = [
        line for name, kind in walk.before for line in _step(name, kind, met, role)
    ]
    opening.extend(
        _step(
            walk.marker, walk.marker_kind, met, role, into=walk.marker_kind != "Named"
        )
    )

    decided: list[Line] = [*_step(plan.at, walk.loop[plan.at], met, role)]
    met.met(plan.router, walk.loop[plan.router])
    decided.append(Call(role, plan.router, f"{plan.router}(state)"))
    decided.append(
        Reply(plan.router, role, " | ".join(route for route, _ in plan.routes))
    )
    operands = tuple(
        (
            route,
            tuple(
                line
                for node in plan.chain(target)
                for line in _step(node, walk.loop[plan.nodes[node]], met, role)
            ),
        )
        for route, target in plan.routes
    )
    decided.append(Fragment("alt", operands))

    rounds: Line = Fragment("loop", ((plan.keeps_going, tuple(decided)),))
    entered: list[Line] = [rounds]
    if plan.opening is not None:
        # The fork at the marker: the rounds are entered only where the opening route
        # says so, and a turn answered before them goes straight on to what follows.
        met.met(plan.opening.router, walk.loop.get(plan.opening.router, ""))
        entered = [
            Call(role, plan.opening.router, f"{plan.opening.router}(state)"),
            Reply(
                plan.opening.router,
                role,
                " | ".join(route for route, _ in plan.opening.routes),
            ),
            Fragment("alt", ((plan.opening.entering(plan.nodes), (rounds,)),)),
        ]

    closing: list[Line] = [
        line for name, kind in walk.after for line in _step(name, kind, met, role)
    ]
    answered = _returned(GRAPH_PORT, "GraphRunner", "run")
    return Sequence(
        name="round",
        lifelines=met.drawn(),
        lines=(
            Call("agent", role, _signature(GRAPH_PORT, "GraphRunner", "run")),
            *opening,
            *entered,
            *closing,
            Reply(role, "agent", answered),
        ),
    )


def turn() -> Sequence:
    """A turn as a frontend asks for one, off `Agent.answer`."""
    return _entered(AGENT, "Agent", "answer", "agent", name="turn")
