import ast
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path

ROOT = Path(__file__).parent.parent
SRC = ROOT / "src"
ASSEMBLY = SRC / "cora" / "app" / "assembly.py"
PORTS = SRC / "cora" / "ports"
MAP = ROOT / "docs" / "assets" / "component-map.svg"

ENGINE = "cora.engine"
APP = "cora.app"
DOMAIN = "cora.domain"
ADAPTERS = "cora.adapters"
PLUGINS = "cora.plugins"
FRONTENDS = "cora.frontends"

# Where each drawn package keeps its source. `cora.ports` is not among them: its
# Protocols are drawn as the interfaces on the connectors; a box would draw them twice.
TREES = {
    FRONTENDS: ("frontends",),
    PLUGINS: ("plugins",),
    ENGINE: ("src", "cora", "engine"),
    ADAPTERS: ("src", "cora", "adapters"),
    APP: ("src", "cora", "app"),
    DOMAIN: ("src", "cora", "domain"),
}
# `assemble` takes the factory; the engine holds the runner it returns, and that is the
# interface a reader of the map is looking for.
AS_DRAWN = {"GraphFor": "GraphRunner"}
# Two slots the engine talks through that are not arguments to `assemble`: the loader
# registry is fixed at the composition root, and a plugin arrives in the plugin set.
BESIDE_THE_SIGNATURE = ("Loader", "Plugin")


@dataclass(frozen=True)
class Binding:
    """One interface the engine requires, and the components that provide it."""

    port: str
    providers: tuple[str, ...]
    package: str


def _tree(name: str) -> Path:
    return ROOT.joinpath(*TREES[name])


def _modules(name: str) -> list[Path]:
    return [
        module
        for module in sorted(_tree(name).rglob("*.py"))
        if "node_modules" not in module.parts
    ]


def _parsed(path: Path) -> ast.Module:
    return ast.parse(path.read_text())


def _imported(tree: ast.Module) -> dict[str, str]:
    return {
        alias.asname or alias.name: node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }


def _function(tree: ast.Module, name: str) -> ast.FunctionDef:
    return next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    )


def _protocols(path: Path) -> set[str]:
    return {
        node.name
        for node in _parsed(path).body
        if isinstance(node, ast.ClassDef)
        and any(
            isinstance(base, ast.Name) and base.id == "Protocol" for base in node.bases
        )
    }


def declared_ports() -> set[str]:
    return {name for path in PORTS.glob("*.py") for name in _protocols(path)}


def _named(annotation: ast.expr | None) -> set[str]:
    if annotation is None:
        return set()
    return {node.id for node in ast.walk(annotation) if isinstance(node, ast.Name)}


def _slots(tree: ast.Module) -> list[tuple[str, str]]:
    ports = declared_ports()
    found = []
    for argument in _function(tree, "assemble").args.kwonlyargs:
        for name in sorted(_named(argument.annotation)):
            drawn = AS_DRAWN.get(name, name)
            if name in ports or drawn in ports:
                found.append((argument.arg, drawn))
    return found


def _called(node: ast.expr) -> str | None:
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            if node.func.id == "partial" and node.args:
                return _called(node.args[0])
            return node.func.id
        if isinstance(node.func, ast.Attribute) and isinstance(
            node.func.value, ast.Name
        ):
            return node.func.value.id
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return _called(node.value)
    return None


def _locals(build: ast.FunctionDef) -> dict[str, str]:
    bound = {}
    for node in ast.walk(build):
        if (
            isinstance(node, ast.Assign)
            and isinstance(node.targets[0], ast.Name)
            and (filled := _called(node.value))
        ):
            bound[node.targets[0].id] = filled
    return bound


def _provider(name: str, imported: dict[str, str]) -> str:
    """Past a factory to the class it returns: `langgraph_for` is how the runner is
    made, `LangGraphRunner` is what stands behind the interface.
    """
    module = imported.get(name, "")
    if not module.startswith("cora."):
        return name
    source = SRC.joinpath(*module.split(".")).with_suffix(".py")
    if not source.exists():
        return name
    returned = [
        made
        for node in _parsed(source).body
        if isinstance(node, ast.FunctionDef) and node.name == name
        for statement in ast.walk(node)
        if isinstance(statement, ast.Return) and statement.value is not None
        for made in (_called(statement.value),)
        if made
    ]
    return returned[0] if returned else name


def _assembled(tree: ast.Module) -> dict[str, str]:
    build = _function(tree, "build")
    call = next(
        node
        for node in ast.walk(build)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "assemble"
    )
    resolved = _locals(build)
    imported = _imported(tree)
    filled = {}
    for keyword in call.keywords:
        if keyword.arg and (name := _called(keyword.value)):
            filled[keyword.arg] = _provider(resolved.get(name, name), imported)
    return filled


def _registry_module(tree: ast.Module) -> str:
    """The module the loader registry lives in. The loaders are functions and a function
    is no component, so the module that holds them is what provides `Loader`.
    """
    return _imported(tree)["LOADERS"].rsplit(".", 1)[-1]


def _packages(name: str) -> tuple[str, ...]:
    return tuple(sorted(path.name for path in _tree(name).iterdir() if path.is_dir()))


def bindings() -> tuple[Binding, ...]:
    tree = _parsed(ASSEMBLY)
    filled = _assembled(tree)
    bound = [
        Binding(port, (filled[slot],), ADAPTERS)
        for slot, port in _slots(tree)
        if slot in filled
    ]
    beside = {
        "Loader": Binding("Loader", (_registry_module(tree),), ADAPTERS),
        "Plugin": Binding("Plugin", _packages(PLUGINS), PLUGINS),
    }
    return tuple(bound) + tuple(beside[port] for port in BESIDE_THE_SIGNATURE)


def _parents(node: ast.AST) -> dict[ast.AST, ast.AST]:
    return {
        child: parent
        for parent in ast.walk(node)
        for child in ast.iter_child_nodes(parent)
    }


def _role(call: ast.Call, parents: dict[ast.AST, ast.AST]) -> str | None:
    """What the engine calls this part: the keyword it is passed as, or the name it is
    assigned to. A part is drawn `role: Type`, so the role comes off the source as well.
    """
    node: ast.AST = call
    while node in parents:
        parent = parents[node]
        if isinstance(parent, ast.keyword) and parent.arg:
            return parent.arg
        if isinstance(parent, ast.Assign) and isinstance(parent.targets[0], ast.Name):
            return parent.targets[0].id
        node = parent
    return None


def engine_parts() -> tuple[tuple[str, str], ...]:
    """The parts `assemble` always builds, as `role: Type` in the order it reads them.
    The debug wrappers are not among them: they stand behind an `if`, around a port.
    """
    tree = _parsed(ASSEMBLY)
    imported = _imported(tree)
    assemble = _function(tree, "assemble")
    parents = _parents(assemble)
    found = []
    for statement in assemble.body:
        if isinstance(statement, ast.If):
            continue
        for node in ast.walk(statement):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and imported.get(node.func.id, "").startswith(ENGINE)
                and (role := _role(node, parents))
            ):
                found.append((node.lineno, node.col_offset, role, node.func.id))
    return tuple(dict.fromkeys((role, kind) for _, _, role, kind in sorted(found)))


def frontends() -> tuple[str, ...]:
    return _packages(FRONTENDS)


def dependencies() -> frozenset[tuple[str, str]]:
    """Which drawn package imports which, off every `from cora.…` in their trees."""
    found = set()
    for client in TREES:
        for module in _modules(client):
            for node in ast.walk(_parsed(module)):
                if not isinstance(node, ast.ImportFrom) or not node.module:
                    continue
                supplier = ".".join(node.module.split(".")[:2])
                if supplier in TREES and supplier != client:
                    found.add((client, supplier))
    return frozenset(found)


STYLE = """
  <style>
    text { font: 13px/1.4 -apple-system, "Segoe UI", Roboto, sans-serif; fill: #202124 }
    .stereotype { font-size: 10.5px; fill: #5f6368; letter-spacing: .04em }
    .name { font-weight: 600 }
    .role { font-size: 12px }
    .engine { fill: #f6f4ff; stroke: #6c5ce7; stroke-width: 1.8 }
    .part { fill: #ffffff; stroke: #6c5ce7; stroke-width: 1.2 }
    .part-name { fill: #4b3fbb }
    .frame { fill: none; stroke: #9aa0a6; stroke-width: 1.1; stroke-dasharray: 3 3 }
    .outer { fill: #ffffff; stroke: #9aa0a6; stroke-width: 1.4 }
    .wire { stroke: #9aa0a6; stroke-width: 1.3; fill: none }
    .socket { stroke: #9aa0a6; stroke-width: 1.6; fill: none }
    .ball { fill: #ffffff; stroke: #9aa0a6; stroke-width: 1.6 }
    .port { fill: #6b7280; font-size: 12px }
    .imports { stroke: #8f96a3; stroke-width: 1.3; fill: none;
               stroke-dasharray: 6 4; marker-end: url(#import) }
    .import-label { fill: #6b7280; font-size: 10.5px; letter-spacing: .04em }
    @media (prefers-color-scheme: dark) {
      text { fill: #e8eaed }
      .stereotype { fill: #9aa0a6 }
      .engine { fill: #2a2550; stroke: #a99cff }
      .part { fill: #35306080; stroke: #a99cff }
      .part-name { fill: #cfc7ff }
      .outer { fill: #303134; stroke: #9aa0a6 }
      .ball { fill: #303134 }
    }
  </style>
"""

WIDTH = 1200.0
LEFT_X, LEFT_W = 34.0, 236.0
ENGINE_X, ENGINE_W = 384.0, 300.0
RIGHT_X, RIGHT_W = 872.0, 296.0
MEMBER = 46.0
GAP = 10.0
FRAME_HEAD = 30.0
TOP = 46.0


@dataclass(frozen=True)
class Box:
    x: float
    y: float
    w: float
    h: float

    @property
    def right(self) -> float:
        return self.x + self.w

    @property
    def bottom(self) -> float:
        return self.y + self.h

    @property
    def mid_x(self) -> float:
        return self.x + self.w / 2

    @property
    def mid_y(self) -> float:
        return self.y + self.h / 2


def _framed(x: float, y: float, w: float, count: int) -> Box:
    return Box(x, y, w, count * (MEMBER + GAP) - GAP + FRAME_HEAD + GAP)


def _member(frame: Box, index: int) -> Box:
    return Box(
        frame.x + 12,
        frame.y + FRAME_HEAD + index * (MEMBER + GAP),
        frame.w - 24,
        MEMBER,
    )


def _text(x: float, y: float, value: str, style: str, anchor: str = "middle") -> str:
    return (
        f'  <text x="{x:g}" y="{y:g}" class="{style}" text-anchor="{anchor}">'
        f"{value}</text>"
    )


def _rect(box: Box, style: str, radius: float = 4.0) -> str:
    return (
        f'  <rect x="{box.x:g}" y="{box.y:g}" width="{box.w:g}" height="{box.h:g}"'
        f' rx="{radius:g}" class="{style}"/>'
    )


def _component(box: Box, name: str, style: str = "outer") -> list[str]:
    return [
        _rect(box, style),
        _text(box.mid_x, box.y + 19, "«component»", "stereotype"),
        _text(box.mid_x, box.y + 36, name, "name"),
    ]


def _frame(box: Box, name: str) -> list[str]:
    return [
        _rect(box, "frame"),
        _text(box.x + 10, box.y + 18, f"«package» {name}", "stereotype", "start"),
    ]


def _path(points: list[tuple[float, float]], style: str) -> str:
    head, *rest = points
    drawn = f"M {head[0]:g} {head[1]:g} " + " ".join(f"L {x:g} {y:g}" for x, y in rest)
    return f'  <path d="{drawn}" class="{style}"/>'


def _imports(points: list[tuple[float, float]]) -> list[str]:
    segments = list(pairwise(points))
    (x1, y1), (x2, y2) = max(
        segments,
        key=lambda pair: abs(pair[0][0] - pair[1][0]) + abs(pair[0][1] - pair[1][1]),
    )
    flat = y1 == y2
    x, y = (x1 + x2) / 2, (y1 + y2) / 2
    aside = 0.0 if flat else (-42.0 if x > WIDTH - 60 else 28.0)
    return [
        _path(points, "imports"),
        _text(x + aside, y - 6 if flat else y, "«import»", "import-label"),
    ]


def _socket(x: float, y: float, port: str, engine_right: float) -> list[str]:
    return [
        _path([(engine_right, y), (x - 13, y)], "wire"),
        f'  <path d="M {x - 13:g} {y - 11:g} A 11 11 0 0 0 {x - 13:g} {y + 11:g}"'
        ' class="socket"/>',
        _text(x - 4, y - 15, port, "port"),
    ]


def _ball(x: float, y: float, to: float) -> list[str]:
    return [
        f'  <circle cx="{x + 4:g}" cy="{y:g}" r="5.5" class="ball"/>',
        _path([(x + 9.5, y), (to, y)], "wire"),
    ]


def svg() -> str:
    bound = bindings()
    parts = engine_parts()
    pages = frontends()
    plugged = _packages(PLUGINS)
    adapters = [
        (binding.port, binding.providers[0])
        for binding in bound
        if binding.package == ADAPTERS
    ]

    adapter_frame = _framed(RIGHT_X, TOP, RIGHT_W, len(adapters))
    plugin_frame = _framed(RIGHT_X, adapter_frame.bottom + 36, RIGHT_W, len(plugged))
    engine = Box(ENGINE_X, TOP, ENGINE_W, plugin_frame.bottom - TOP)
    pitch = (engine.h - 56) / len(parts)
    frontend_frame = _framed(LEFT_X, TOP, LEFT_W, len(pages))
    app = Box(LEFT_X, frontend_frame.bottom + 96, LEFT_W, MEMBER)
    lane = engine.bottom + 28
    domain = Box(LEFT_X, lane + 32, WIDTH - 2 * LEFT_X, MEMBER)
    height = domain.bottom + TOP

    label = (
        f"cora as a UML component diagram: {len(pages)} frontends, an engine of "
        f"{len(parts)} parts, {len(bound)} required interfaces wired to the components "
        "that provide them, and the packages each one depends on. Generated by "
        "scripts/gen_component_map.py."
    )
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH:g} {height:g}"'
        f' width="{WIDTH:g}" height="{height:g}" role="img" aria-label="{label}">',
        STYLE.strip("\n"),
        '  <defs><marker id="import" viewBox="0 0 10 10" refX="9" refY="5"'
        ' markerWidth="9" markerHeight="9" orient="auto-start-reverse">'
        '<path d="M 0 1 L 9 5 L 0 9" fill="none" stroke="#8f96a3"'
        ' stroke-width="1.4"/></marker></defs>',
    ]

    out += _component(engine, ENGINE, "engine")
    for index, (role, kind) in enumerate(parts):
        part = Box(
            engine.x + 20, engine.y + 50 + index * pitch, engine.w - 40, pitch - 9
        )
        out += [
            _rect(part, "part"),
            _text(part.mid_x, part.mid_y + 4, f"{role}: {kind}", "part-name role"),
        ]

    out += _frame(frontend_frame, FRONTENDS)
    for index, page in enumerate(pages):
        out += _component(_member(frontend_frame, index), page)
    out += _component(app, APP)
    out += _component(domain, DOMAIN)

    out += _frame(adapter_frame, ADAPTERS)
    socket_x = (engine.right + RIGHT_X) / 2
    for index, (port, provider) in enumerate(adapters):
        member = _member(adapter_frame, index)
        out += _component(member, provider)
        out += _socket(socket_x, member.mid_y, port, engine.right)
        out += _ball(socket_x, member.mid_y, member.x)

    out += _frame(plugin_frame, PLUGINS)
    members = [_member(plugin_frame, index) for index in range(len(plugged))]
    for member, plugin in zip(members, plugged, strict=True):
        out += _component(member, plugin)
    shared = sum(member.mid_y for member in members) / len(members)
    out += _socket(socket_x, shared, "Plugin", engine.right)
    fork = socket_x + 44
    out.append(_path([(socket_x - 4, shared), (fork, shared)], "wire"))
    for member in members:
        out += [
            _path([(fork, shared), (fork, member.mid_y)], "wire"),
            *_ball(member.x - 30, member.mid_y, member.x),
            _path([(fork, member.mid_y), (member.x - 30, member.mid_y)], "wire"),
        ]

    routes = {
        (FRONTENDS, ENGINE): [
            (frontend_frame.right, frontend_frame.mid_y),
            (engine.x, frontend_frame.mid_y),
        ],
        (FRONTENDS, APP): [
            (frontend_frame.mid_x, frontend_frame.bottom),
            (frontend_frame.mid_x, app.y),
        ],
        (FRONTENDS, DOMAIN): [
            (frontend_frame.x, frontend_frame.bottom - 16),
            (LEFT_X - 20, frontend_frame.bottom - 16),
            (LEFT_X - 20, domain.mid_y),
            (domain.x, domain.mid_y),
        ],
        (APP, ENGINE): [
            (app.right, app.mid_y),
            (engine.x - 36, app.mid_y),
            (engine.x - 36, engine.mid_y + 60),
            (engine.x, engine.mid_y + 60),
        ],
        (APP, ADAPTERS): [
            (app.mid_x + 44, app.y),
            (app.mid_x + 44, TOP - 30),
            (adapter_frame.mid_x + 70, TOP - 30),
            (adapter_frame.mid_x + 70, adapter_frame.y),
        ],
        (APP, DOMAIN): [
            (app.mid_x, app.bottom),
            (app.mid_x, domain.y),
        ],
        (ENGINE, DOMAIN): [
            (engine.mid_x - 60, engine.bottom),
            (engine.mid_x - 60, domain.y),
        ],
        (ADAPTERS, DOMAIN): [
            (adapter_frame.right, adapter_frame.bottom - 16),
            (WIDTH - 16, adapter_frame.bottom - 16),
            (WIDTH - 16, domain.mid_y),
            (domain.right, domain.mid_y),
        ],
        (PLUGINS, DOMAIN): [
            (plugin_frame.mid_x, plugin_frame.bottom),
            (plugin_frame.mid_x, domain.y),
        ],
        (PLUGINS, ENGINE): [
            (plugin_frame.x, plugin_frame.bottom - 14),
            (plugin_frame.x - 46, plugin_frame.bottom - 14),
            (plugin_frame.x - 46, lane),
            (engine.mid_x + 60, lane),
            (engine.mid_x + 60, engine.bottom),
        ],
    }
    edges = dependencies()
    if unrouted := edges - routes.keys():
        raise SystemExit(f"the source has a dependency the map cannot draw: {unrouted}")
    for edge in sorted(edges):
        out += _imports(routes[edge])

    out.append("</svg>")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    MAP.write_text(svg())
    print(f"wrote {MAP.relative_to(ROOT)}")
