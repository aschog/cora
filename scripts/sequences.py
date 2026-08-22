"""The sequences the docs draw, read out of the code they are about.

A message is a call a method makes, in the order it makes them; a branch is an `alt` and
a loop a `loop`, so what comes out says what the code can do rather than what one run of
it did. Nothing here draws: `gen_session_maps.py` is what turns a `Sequence` into UML.
"""

import ast
from dataclasses import dataclass
from pathlib import Path

import gen_component_map as components

ROOT = Path(__file__).parent.parent
SRC = ROOT / "src"
FRONTENDS = ROOT / "frontends"

# How deep the drawing follows an object into its own work. A private method is no
# participant — it is the object's own work, so its calls are drawn on the object's own
# lifeline — and the cap is what keeps a cycle from being drawn forever.
DEPTH = 3


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


def _parsed(path: Path) -> ast.Module:
    return ast.parse(path.read_text())


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
    """The name an annotation leads with: `Memory | None` is a memory slot."""
    if isinstance(annotation, ast.BinOp):
        return _head(annotation.left)
    if isinstance(annotation, ast.Subscript):
        return _head(annotation.value)
    return ast.unparse(annotation).rsplit(".", 1)[-1].strip("'\"")


def _fields(klass: ast.ClassDef) -> dict[str, str]:
    """The annotated fields of a class, which is what its lifelines are drawn from."""
    return {
        node.target.id: _head(node.annotation)
        for node in klass.body
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    }


def providers() -> dict[str, str]:
    """What fills each port, off the composition root — the component map's own reading.

    A lifeline says what is really there: `retriever: ChromaRetriever`, because a
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

    @property
    def drawn(self) -> str:
        return providers().get(self.kind, self.kind)


def _element(annotation: ast.expr) -> str:
    """What one of a container holds: a rule out of `tuple[ValidationRule, ...]`."""
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
    """What one call answers with, off the signature of the interface it is made on."""
    path = _module(module)
    if not path.exists():
        return ""
    try:
        found = _method(_klass(_parsed(path), kind), method)
    except StopIteration:
        return ""
    return "" if found.returns is None else ast.unparse(found.returns)


def _argument(node: ast.expr) -> str:
    """One name as the source writes it, with `self.` left off: the reader knows."""
    written = ast.unparse(node).replace("self.", "")
    return written[1:-1] if isinstance(node, ast.Tuple) else written


def _named(node: ast.expr) -> str:
    """An argument that is itself a call is named rather than written out: the message
    it stands for is drawn on its own line already."""
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
# The one binding no single file states: `assemble` hands `_offered_tools` the knowledge
# base and `_offered_tools` hands `search_tool` a `ContextSource`, so the class behind
# the tool's interface is three calls away from the annotation that names it. A guard
# fails if `KnowledgeBase` stops answering for it.
BEHIND = {"ContextSource": "KnowledgeBase"}


def engine_classes() -> dict[str, str]:
    """Every class `cora.engine` declares, and the module it is declared in.

    What the drawing may open: a class of the engine is cora's own work, so its calls
    belong on the drawing. An adapter is a boundary — opening one would draw a library.
    """
    return {
        node.name: f"cora.engine.{path.stem}"
        for path in sorted(ENGINE.glob("*.py"))
        for node in _parsed(path).body
        if isinstance(node, ast.ClassDef)
    }


def _port_modules() -> dict[str, str]:
    return {
        node.name: f"cora.ports.{path.stem}"
        for path in sorted((SRC / "cora" / "ports").glob("*.py"))
        for node in _parsed(path).body
        if isinstance(node, ast.ClassDef)
    }


def wired() -> dict[str, str]:
    """What the composition root drops into each slot it fills by name.

    Some slots are told apart by their type and some only by their role: two of the
    runner's are `Step`, and the tool runtime arrives as the `ToolExecutor` it answers
    for. What fills them is a keyword in `assemble`, so that is where it is read.
    """
    tree = _parsed(_module(ASSEMBLY))
    found: dict[str, str] = {}
    for call in _ordered(components._function(tree, "assemble")):
        for keyword in call.keywords:
            filling = components._called(keyword.value)
            if keyword.arg and filling and filling[0].isupper():
                found[keyword.arg] = filling
    return found


def drawn_kind(kind: str, role: str = "") -> str:
    """What a slot really holds in a running app, by its role and then by its type."""
    return wired().get(role) or providers().get(kind) or BEHIND.get(kind, kind)


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
    """What a `for` walks, so the loop variable is typed by one of what it holds."""
    if isinstance(node, ast.Attribute) and node.attr in held:
        return _element(held[node.attr])
    if isinstance(node, ast.Name):
        return scope.get(node.id, "")
    return ""


def _stops(body: list[ast.stmt]) -> bool:
    """Whether a branch leaves the method, which makes the rest of it the other path."""
    return any(isinstance(node, ast.Return | ast.Raise) for node in body)


def _ordered(node: ast.AST) -> list[ast.Call]:
    """Every call one statement makes, innermost first — the order they happen in.

    A call written around another runs after it: `self._turn(self.runner.run(…))` sends
    the run and then the turn, which is the opposite of the order they are read in.
    """
    found: list[ast.Call] = []
    for child in ast.iter_child_nodes(node):
        found.extend(_ordered(child))
    if isinstance(node, ast.Call):
        found.append(node)
    return found


SIGNATURE = "\x00signature"
"""A reply the drawing takes off the signature rather than off a name: a value that is
returned or tested is never bound to anything the source could be asked for."""


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
    dotted: str, kind: str, method: str, role: str, met: Reading, depth: int = 0
) -> tuple[Line, ...]:
    """One method as the messages it sends, in the order the body sends them.

    A branch becomes an `alt` and a loop a `loop`, so what the drawing shows is what the
    code can do rather than one run of it. A call the object makes on itself is followed
    into: a private method is the object's own work, not another participant.
    """
    tree = _parsed(_module(dotted))
    klass = _klass(tree, kind)
    body = _method(klass, method)
    imported = components._imported(tree)
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

    def emit(call: ast.Call, reply: str) -> list[Line]:
        found = receiver_of(call)
        if found is None:
            return []
        name, message = found
        slot = slots.get(name)
        typed = slot.kind if slot else scope.get(name, "")
        drawn = drawn_kind(kind, role) if name == role else drawn_kind(typed, name)
        where = slot.declared_in if slot else imported.get(name, "")
        if name != role and not a_participant(drawn, where):
            return []
        met.met(name, drawn)
        lines: list[Line] = [Call(role, name, _label(call, message))]
        answered = "" if name == role else reply
        if answered == SIGNATURE:
            answered = (
                _returned(slot.declared_in, typed, message)
                if slot and slot.declared_in
                else ""
            )
        opened = drawn
        if depth < DEPTH:
            if name == role and message.startswith("_"):
                lines.extend(read(dotted, kind, message, role, met, depth + 1))
            elif opened in engine_classes() and opened != kind:
                lines.extend(
                    read(
                        engine_classes()[opened], opened, message, name, met, depth + 1
                    )
                )
        # After whatever the call set off, never before it: a reply closes a message.
        if answered:
            lines.append(Reply(name, role, answered))
        return lines

    def sent(node: ast.AST, reply: str) -> list[Line]:
        """Every message one statement sends. What it answers with belongs to the first
        of them: a statement binds one value, and the message that fetched it is the
        one the value comes back along."""
        out: list[Line] = []
        for call in _ordered(node):
            found = emit(call, reply if not out else "")
            out += found
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
                    rest = walk([*node.orelse, *statements[index + 1 :]])
                    if speaks(taken):
                        operands = ((_guard(node.test), taken), ("else", rest))
                        out.append(Fragment("alt", operands))
                    else:
                        # A branch nobody hears from is a guard clause, not a fork:
                        # there is no interaction on it to draw, so the drawing carries
                        # on the way that has one.
                        out.extend(rest)
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
            if isinstance(node, ast.Try):
                out += walk(node.body)
                for handler in node.handlers:
                    out += walk(handler.body)
                continue
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
        for node in _ordered(_parsed(path))
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
    """A call as its own parameters name it, which is what the caller has to pass."""
    body = _method(_klass(_parsed(_module(dotted)), kind), method)
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
    """One drawing, from the call that opens it: whoever calls the method, then it.

    `by` names the caller where no call site states it — a tool is reached through the
    port that holds it, so no source mentions the class the runtime is about to run.
    """
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
    tree = _parsed(_module(dotted))
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


def graph_steps() -> dict[str, str]:
    """What the composition root drops into each of the runner's slots.

    Every one of them is typed `Step`, so what fills one is known by the name it is
    passed under and by nothing else — a slot is told apart by its role here, where a
    port elsewhere is told apart by its type.
    """
    tree = _parsed(_module(ASSEMBLY))
    built = next(
        node
        for node in ast.walk(components._function(tree, "assemble"))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == GRAPH
    )
    named = {
        keyword.arg: components._called(keyword.value)
        for keyword in built.keywords
        if keyword.arg
    }
    return {role: kind for role, kind in named.items() if kind and kind[0].isupper()}


@dataclass(frozen=True)
class Routing:
    """The graph the runner declares: what each node runs, and what leads where."""

    nodes: dict[str, str]
    edges: tuple[tuple[str, str], ...]
    at: str
    router: str
    routes: tuple[tuple[str, str], ...]

    def after(self, node: str) -> str:
        return next((there for here, there in self.edges if here == node), "")

    def chain(self, start: str) -> tuple[str, ...]:
        """The nodes one route leads through before the decision is taken again."""
        walked: list[str] = []
        node = start
        while node in self.nodes and node != self.at and node not in walked:
            walked.append(node)
            node = self.after(node)
        return tuple(walked)


def _value(tree: ast.Module, imported: dict[str, str], name: str) -> str:
    """A node's name as the string it stands for, wherever the constant is declared."""
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
    return (_parsed(_module(module)),)


def routing() -> Routing:
    """The graph, read off the builder the runner hands to LangGraph.

    Nodes and edges are the runner's own statements — what it says the turn's shape is —
    so the drawing takes the shape from there rather than from any run of it.
    """
    tree = _parsed(_module(RUNNER))
    imported = components._imported(tree)
    body = _method(_klass(tree, "LangGraphRunner"), "_graph")
    nodes: dict[str, str] = {}
    edges: list[tuple[str, str]] = []
    at = router = ""
    routes: tuple[tuple[str, str], ...] = ()

    def named(node: ast.expr) -> str:
        return _value(tree, imported, node.id) if isinstance(node, ast.Name) else ""

    for call in _ordered(body):
        if not isinstance(call.func, ast.Attribute):
            continue
        held = call.func.value
        if not isinstance(held, ast.Name) or held.id != BUILDER:
            continue
        if call.func.attr == "add_node":
            nodes[named(call.args[0])] = _role_of(call.args[1])
        elif call.func.attr == "add_edge":
            edges.append((named(call.args[0]), named(call.args[1])))
        elif call.func.attr == "add_conditional_edges":
            at = named(call.args[0])
            router = _role_of(call.args[1])
            mapped = call.args[2]
            assert isinstance(mapped, ast.Dict)
            routes = tuple(
                (named(key), named(value))
                for key, value in zip(mapped.keys, mapped.values, strict=True)
                if key is not None
            )
    return Routing(nodes, tuple(edges), at, router, routes)


def _role_of(node: ast.expr) -> str:
    """Which of the runner's own slots a node runs: `self.model(on_text)` is `model`."""
    if isinstance(node, ast.Call):
        return _role_of(node.func)
    if isinstance(node, ast.Attribute):
        return node.attr
    return _argument(node)


GRAPH_PORT = "cora.ports.graph"
KEEPS_GOING = 'router(state) != "done"'
"""What the graph says a round is: every route but one leads back to the model, and the
one that does not is the answer. The condition is the edge map read as a sentence."""


def _step(plan: Routing, node: str, met: Reading, role: str) -> list[Line]:
    """One node of the graph: the step it runs, and what that step does."""
    slot = plan.nodes[node]
    kind = graph_steps()[slot]
    met.met(slot, kind)
    lines: list[Line] = [Call(role, slot, f"{slot}(state)")]
    where = engine_classes().get(kind)
    if where:
        lines.extend(read(where, kind, "__call__", slot, met, 1))
    lines.append(Reply(slot, role, _returned(GRAPH_PORT, "Step", "__call__")))
    return lines


def round_taken() -> Sequence:
    """A turn as the graph walks it, off the nodes and edges the runner declares."""
    plan = routing()
    met = Reading({})
    role = "runner"
    met.met("agent", "Agent")
    met.met(role, providers()["GraphRunner"])

    opening: list[Line] = []
    node = plan.after("START")
    while node and node != plan.at:
        opening.extend(_step(plan, node, met, role))
        node = plan.after(node)

    decided: list[Line] = [*_step(plan, plan.at, met, role)]
    met.met(plan.router, graph_steps()[plan.router])
    decided.append(Call(role, plan.router, f"{plan.router}(state)"))
    decided.append(
        Reply(plan.router, role, " | ".join(route for route, _ in plan.routes))
    )
    operands = tuple(
        (
            route,
            tuple(
                line
                for step in plan.chain(target)
                for line in _step(plan, step, met, role)
            ),
        )
        for route, target in plan.routes
    )
    decided.append(Fragment("alt", operands))

    answered = _returned(GRAPH_PORT, "GraphRunner", "run")
    return Sequence(
        name="round",
        lifelines=met.drawn(),
        lines=(
            Call("agent", role, _signature(GRAPH_PORT, "GraphRunner", "run")),
            *opening,
            Fragment("loop", ((KEEPS_GOING, tuple(decided)),)),
            Reply(role, "agent", answered),
        ),
    )


def turn() -> Sequence:
    """A turn as a frontend asks for one, off `Agent.answer`."""
    return _entered(AGENT, "Agent", "answer", "agent", name="turn")
