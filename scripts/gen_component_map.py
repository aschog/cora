import ast
from dataclasses import dataclass
from pathlib import Path

import reading

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
# registry is fixed at the composition root, and a plugin arrives as a module that
# registers what it has.
BESIDE_THE_SIGNATURE = ("Loader", "Extension")


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


def _protocols(path: Path) -> set[str]:
    return {
        node.name
        for node in reading.parsed(path).body
        if isinstance(node, ast.ClassDef)
        and any(
            isinstance(base, ast.Name) and base.id == "Protocol" for base in node.bases
        )
    }


def declared_ports() -> set[str]:
    return {name for path in PORTS.glob("*.py") for name in _protocols(path)}


def declaring_modules() -> dict[str, str]:
    """Which module of `cora.ports` declares each interface. `__init__` re-exports
    nothing, so the module is part of the name a reader would import.
    """
    return {
        node.name: f"cora.ports.{path.stem}"
        for path in sorted(PORTS.glob("*.py"))
        for node in reading.parsed(path).body
        if isinstance(node, ast.ClassDef)
    }


def _named(annotation: ast.expr | None) -> set[str]:
    if annotation is None:
        return set()
    return {node.id for node in ast.walk(annotation) if isinstance(node, ast.Name)}


def _slots(tree: ast.Module) -> list[tuple[str, str]]:
    ports = declared_ports()
    found = []
    for argument in reading.function(tree, "assemble").args.kwonlyargs:
        for name in sorted(_named(argument.annotation)):
            drawn = AS_DRAWN.get(name, name)
            if name in ports or drawn in ports:
                found.append((argument.arg, drawn))
    return found


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
        for node in reading.parsed(source).body
        if isinstance(node, ast.FunctionDef) and node.name == name
        for statement in ast.walk(node)
        if isinstance(statement, ast.Return) and statement.value is not None
        for made in (reading.called(statement.value),)
        if made
    ]
    return returned[0] if returned else name


def _assembled(tree: ast.Module) -> dict[str, str]:
    composer = reading.function(tree, "_composer")
    call = next(
        node
        for node in ast.walk(composer)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "assemble"
    )
    resolved = reading.bound(composer)
    imported = reading.imported(tree)
    filled = {}
    for keyword in call.keywords:
        if keyword.arg and (name := reading.called(keyword.value)):
            filled[keyword.arg] = _provider(resolved.get(name, name), imported)
    return filled


def _registry_module(tree: ast.Module) -> str:
    """The module the loader registry lives in. The loaders are functions and a function
    is no component, so the module that holds them is what provides `Loader`.
    """
    return reading.imported(tree)["LOADERS"].rsplit(".", 1)[-1]


def _packages(name: str) -> tuple[str, ...]:
    return tuple(sorted(path.name for path in _tree(name).iterdir() if path.is_dir()))


def bindings() -> tuple[Binding, ...]:
    tree = reading.parsed(ASSEMBLY)
    filled = _assembled(tree)
    bound = [
        Binding(port, (filled[slot],), ADAPTERS)
        for slot, port in _slots(tree)
        if slot in filled
    ]
    beside = {
        "Loader": Binding("Loader", (_registry_module(tree),), ADAPTERS),
        "Extension": Binding("Extension", _packages(PLUGINS), PLUGINS),
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
    tree = reading.parsed(ASSEMBLY)
    imported = reading.imported(tree)
    assemble = reading.function(tree, "assemble")
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
            for node in ast.walk(reading.parsed(module)):
                if not isinstance(node, ast.ImportFrom) or not node.module:
                    continue
                supplier = ".".join(node.module.split(".")[:2])
                if supplier in TREES and supplier != client:
                    found.add((client, supplier))
    return frozenset(found)


STYLE = """
  <style>
    text { font: 13px/1.4 -apple-system, "Segoe UI", Roboto, sans-serif; fill: #202124 }
    .stereotype { font-size: 11px; fill: #5f6368; letter-spacing: .03em }
    .name { font-weight: 600 }
    .role { font-size: 12.5px }
    .engine { fill: #f2f8fd; stroke: #2b7fc4; stroke-width: 1.6 }
    .part { fill: #ffffff; stroke: #2b7fc4; stroke-width: 1.1 }
    .part-name { fill: #14425f }
    .frame { fill: #f8f9fa; stroke: #9aa0a6; stroke-width: 1.1 }
    .outer { fill: #ffffff; stroke: #5f6368; stroke-width: 1.3 }
    .glyph { fill: #ffffff; stroke: #5f6368; stroke-width: 1.1 }
    .glyph-engine { fill: #f2f8fd; stroke: #2b7fc4; stroke-width: 1.1 }
    .socket-port { fill: #f2f8fd; stroke: #2b7fc4; stroke-width: 1.4 }
    .wire { stroke: #5f6368; stroke-width: 1.3; fill: none }
    .socket { stroke: #5f6368; stroke-width: 1.5; fill: none }
    .ball { fill: #ffffff; stroke: #5f6368; stroke-width: 1.5 }
    .port { fill: #202124; font-size: 13px; font-weight: 600 }
    .multiplicity { fill: #5f6368; font-size: 11.5px; font-style: italic }
    .imports { stroke: #8f96a3; stroke-width: 1.2; fill: none;
               stroke-dasharray: 6 4; marker-end: url(#import) }
    .import-label { fill: #6b7280; font-size: 11px; font-style: italic }
    @media (prefers-color-scheme: dark) {
      text { fill: #e8eaed }
      .stereotype { fill: #9aa0a6 }
      .port { fill: #e8eaed }
      .engine { fill: #10283a; stroke: #6fb6ea }
      .part { fill: #1b2b3480; stroke: #6fb6ea }
      .part-name { fill: #cfe6f7 }
      .frame { fill: #2b2c2f; stroke: #9aa0a6 }
      .outer { fill: #303134; stroke: #bdc1c6 }
      .glyph { fill: #303134; stroke: #bdc1c6 }
      .glyph-engine { fill: #10283a; stroke: #6fb6ea }
      .socket-port { fill: #10283a; stroke: #6fb6ea }
      .wire, .socket { stroke: #bdc1c6 }
      .ball { fill: #303134; stroke: #bdc1c6 }
    }
  </style>
"""

MARGIN = 24.0
# One required interface per row, and the row is the unit the whole drawing is built on:
# the component that provides it, the port it leaves the engine by, and its name all sit
# on the same line, so a reader follows one interface across without tracking a bend.
ROW = 92.0
MEMBER_H = 52.0
PART_H = 46.0
TAB_H = 22.0
FRAME_PAD = 16.0
COLUMN_GAP = 68.0
# The width kept clear between the engine and the components it is wired to: the
# names of the interfaces are read here, so nothing is drawn through it.
CHANNEL = 300.0
# Above the drawing, for the one import that carries a sentence.
NOTE_BAND = 78.0
BAR_H = 62.0
# Under the packages, for the arrows into `cora.domain`.
BAR_GAP = 118.0

CUP = 11.0
BALL = 7.0
# How far the glyph is seated from the component that provides the interface, so the
# wire is drawn on both sides of it: an interface is where two components meet, and
# neither of them owns it.
SEAT = 62.0
ICON = 14.0


@dataclass(frozen=True)
class Box:
    """Where one box sits, in the coordinates the drawing uses."""

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


@dataclass(frozen=True)
class Plan:
    """Every box and every row of the map, placed.

    The arrangement is fixed here rather than searched for: the map has one shape —
    the frontends and the composition root on the left, the engine in the middle, one
    row per required interface out to the right, and `cora.domain` under all of it — so
    a reader who has seen it once finds the same thing in the same place next time.
    """

    width: float
    height: float
    frames: dict[str, Box]
    boxes: dict[str, Box]
    parts: dict[str, Box]
    rows: dict[str, float]
    domain: Box


def _wide(text: str, size: float = 13.0, bold: bool = False) -> float:
    """Roughly how wide a label draws, so a box is made wide enough for its text."""
    per = 0.58 if bold else 0.62 if size < 12 else 0.54
    return len(text) * size * per


def _stack(top: float, count: int) -> list[float]:
    """The tops of `count` boxes on the row pitch, starting at `top`."""
    return [top + index * ROW for index in range(count)]


def _framed(rows: int) -> float:
    """How tall a package frame is that holds `rows` members on the row pitch."""
    return TAB_H + FRAME_PAD + (rows - 1) * ROW + MEMBER_H + FRAME_PAD


def plan() -> Plan:
    """Place every box, off what the source said is in the drawing."""
    bound = bindings()
    outward = [binding for binding in bound if binding.package == ADAPTERS]
    plugged = _packages(PLUGINS)
    pages = frontends()
    parts = engine_parts()

    page_w = max(_wide(page, bold=True) for page in pages) + 96
    provider_w = max(_wide(binding.providers[0], bold=True) for binding in outward) + 92
    plugin_w = max(_wide(name, bold=True) for name in plugged) + 92
    part_w = max(_wide(f"{role}: {kind}", 12.5) for role, kind in parts) + 44

    plugins_w = plugin_w + 2 * FRAME_PAD
    # The adapters' own arrow down to `cora.domain` passes the plugins frame on the way,
    # so the wider frame keeps a lane open beside the narrower one.
    adapters_w = max(provider_w + 2 * FRAME_PAD, plugins_w + 72)

    frontends_box = Box(MARGIN, 0.0, page_w + 2 * FRAME_PAD, _framed(len(pages)))
    app = Box(
        frontends_box.right + COLUMN_GAP, 0.0, _wide(APP, bold=True) + 112, MEMBER_H
    )
    engine_x = app.right + COLUMN_GAP
    engine_w = part_w + 44

    adapters = Box(
        engine_x + engine_w + CHANNEL,
        MARGIN + NOTE_BAND,
        adapters_w,
        _framed(len(outward)),
    )
    tops = _stack(adapters.y + TAB_H + FRAME_PAD, len(outward))
    rows = {
        binding.port: top + MEMBER_H / 2
        for binding, top in zip(outward, tops, strict=True)
    }
    boxes = {
        binding.providers[0]: Box(adapters.x + FRAME_PAD, top, provider_w, MEMBER_H)
        for binding, top in zip(outward, tops, strict=False)
    }

    plugins = Box(adapters.x, adapters.bottom + 26, plugins_w, _framed(len(plugged)))
    plugin_tops = _stack(plugins.y + TAB_H + FRAME_PAD, len(plugged))
    boxes |= {
        name: Box(plugins.x + FRAME_PAD, top, plugin_w, MEMBER_H)
        for name, top in zip(plugged, plugin_tops, strict=False)
    }

    first, last = tops[0] + MEMBER_H / 2, tops[-1] + MEMBER_H / 2
    engine = Box(engine_x, first - 46, engine_w, last + 46 - (first - 46))
    part_tops = _stack(engine.y + 68, len(parts))
    spread = (engine.bottom - 20 - PART_H - part_tops[0]) / (len(parts) - 1)
    parts_placed = {
        role: Box(engine.x + 22, part_tops[0] + index * spread, part_w, PART_H)
        for index, (role, _) in enumerate(parts)
    }

    frontends_box = Box(
        frontends_box.x,
        engine.mid_y - frontends_box.h / 2,
        frontends_box.w,
        frontends_box.h,
    )
    boxes |= {
        page: Box(frontends_box.x + FRAME_PAD, top, page_w, MEMBER_H)
        for page, top in zip(
            pages, _stack(frontends_box.y + TAB_H + FRAME_PAD, len(pages)), strict=False
        )
    }
    app = Box(app.x, engine.mid_y - app.h / 2, app.w, app.h)
    boxes[APP] = app
    boxes[ENGINE] = engine

    domain = Box(
        MARGIN,
        max(plugins.bottom, adapters.bottom) + BAR_GAP,
        adapters.right - MARGIN,
        BAR_H,
    )
    boxes[DOMAIN] = domain
    return Plan(
        width=adapters.right + MARGIN,
        height=domain.bottom + MARGIN,
        frames={FRONTENDS: frontends_box, ADAPTERS: adapters, PLUGINS: plugins},
        boxes=boxes,
        parts=parts_placed,
        rows=rows,
        domain=domain,
    )


def _text(x: float, y: float, value: str, style: str, anchor: str = "middle") -> str:
    return (
        f'  <text x="{x:g}" y="{y:g}" class="{style}" text-anchor="{anchor}">'
        f"{value}</text>"
    )


def _rect(box: Box, style: str, radius: float = 3.0) -> str:
    return (
        f'  <rect x="{box.x:g}" y="{box.y:g}" width="{box.w:g}" height="{box.h:g}"'
        f' rx="{radius:g}" class="{style}"/>'
    )


def _path(points: list[tuple[float, float]], style: str) -> str:
    head, *rest = points
    drawn = f"M {head[0]:g} {head[1]:g} " + " ".join(f"L {x:g} {y:g}" for x, y in rest)
    return f'  <path d="{drawn}" class="{style}"/>'


def _icon(box: Box, style: str = "glyph") -> list[str]:
    """The UML component icon, in the corner a component wears it: the shape is what
    says «component», so the word is not written as well.
    """
    x = box.right - ICON - 14
    y = box.y + 10
    return [
        f'  <rect x="{x:g}" y="{y:g}" width="{ICON:g}" height="14" class="{style}"/>',
        *(
            f'  <rect x="{x - 4:g}" y="{y + dy:g}" width="8" height="4"'
            f' class="{style}"/>'
            for dy in (2.0, 8.0)
        ),
    ]


def _component(box: Box, name: str) -> list[str]:
    return [
        _rect(box, "outer"),
        _text(box.x + 18, box.mid_y + 5, name, "name", "start"),
        *_icon(box),
    ]


def _frame(box: Box, name: str) -> list[str]:
    """A package as UML draws one: the name on its tab, the members in the body."""
    tab = Box(box.x, box.y, _wide(name, 11) + 26, TAB_H)
    body = Box(box.x, box.y + TAB_H, box.w, box.h - TAB_H)
    return [
        _rect(tab, "frame", 2.0),
        _rect(body, "frame"),
        _text(tab.x + 12, tab.y + 15, name, "stereotype", "start"),
    ]


def _port_square(x: float, y: float) -> str:
    """A UML port where a connector leaves the engine: the engine requires what the wire
    carries, and the square is where it is required.
    """
    return (
        f'  <rect x="{x - 5:g}" y="{y - 5:g}" width="10" height="10"'
        ' class="socket-port"/>'
    )


def _cup(x: float, y: float) -> str:
    """The socket of the component that requires the interface, open to the ball."""
    return (
        f'  <path d="M {x:g} {y - CUP:g} A {CUP:g} {CUP:g} 0 0 0 {x:g} {y + CUP:g}"'
        ' class="socket"/>'
    )


def _ball(x: float, y: float) -> str:
    return f'  <circle cx="{x:g}" cy="{y:g}" r="{BALL:g}" class="ball"/>'


def _interface_name(
    x: float, y: float, module: str, port: str, extra: str = ""
) -> list[str]:
    """The interface's qualified name, above the wire it belongs to: the module it is
    declared in over the name the code uses, so both are read off the drawing.
    """
    drawn = [
        _text(x, y - 26, module, "stereotype", "start"),
        _text(x, y - 10, port, "port", "start"),
    ]
    if extra:
        drawn.append(
            _text(
                x + _wide(port, 13, bold=True) + 8,
                y - 10,
                extra,
                "multiplicity",
                "start",
            )
        )
    return drawn


def _assembly(at: Plan, port: str, provider: str, modules: dict[str, str]) -> list[str]:
    """One required interface, drawn on its own row: the engine's port, its socket, the
    ball of the component that provides it, and a stick to each.
    """
    engine = at.boxes[ENGINE]
    box = at.boxes[provider]
    y = at.rows[port]
    ball_x = box.x - SEAT
    return [
        _port_square(engine.right, y),
        _path([(engine.right, y), (ball_x - CUP, y)], "wire"),
        _cup(ball_x, y),
        _ball(ball_x, y),
        _path([(ball_x + BALL, y), (box.x, y)], "wire"),
        *_interface_name(engine.right + 30, y, modules[port], port),
    ]


def _plugin_assembly(
    at: Plan, providers: tuple[str, ...], modules: dict[str, str]
) -> list[str]:
    """The one interface with more than one provider: a single socket on the engine's
    stick, and a ball on every plugin that fills it. `[0..*]` is what the engine takes —
    a plugin set that is empty is a set.
    """
    engine = at.boxes[ENGINE]
    boxes = [at.boxes[name] for name in providers]
    fan_x = min(box.x for box in boxes) - 200
    fan_y = sum(box.mid_y for box in boxes) / len(boxes)
    drop_x = engine.x + engine.w * 0.7
    drawn = [
        _port_square(drop_x, engine.bottom),
        _path([(drop_x, engine.bottom), (drop_x, fan_y), (fan_x - CUP, fan_y)], "wire"),
        _cup(fan_x, fan_y),
        *_interface_name(
            fan_x - CUP - 120, fan_y, modules["Extension"], "Extension", "[0..*]"
        ),
    ]
    for box in boxes:
        ball_x = box.x - 30
        drawn += [
            _path([(fan_x, fan_y), (ball_x - BALL, box.mid_y)], "wire"),
            _ball(ball_x, box.mid_y),
            _path([(ball_x + BALL, box.mid_y), (box.x, box.mid_y)], "wire"),
        ]
    return drawn


# Why one package imports another is the same everywhere but here: `cora.app` is the
# only one that names an adapter, because it is the only one that builds any.
IMPORT = "«import»"


def _centred(left: float, right: float) -> float:
    """Where `«import»` starts for it to sit in the middle of a run that wide."""
    return (left + right) / 2 - _wide(IMPORT, 11) / 2


COMPOSITION_ROOT = (
    "«import» — cora.app is the composition root: it constructs the adapters and the "
    "plugins and injects them at startup"
)


def _route(
    at: Plan, client: str, supplier: str
) -> tuple[list[tuple[float, float]], tuple[float, float]]:
    """The path one import is drawn along, and where its label sits. Every import has a
    lane of its own, so no two are read as one line.
    """
    frames, boxes = at.frames, at.boxes
    app, engine = boxes[APP], boxes[ENGINE]
    if supplier == DOMAIN:
        source = frames.get(client, boxes.get(client))
        assert source is not None
        share = {FRONTENDS: 0.5, APP: 0.5, ENGINE: 0.45, PLUGINS: 0.5}.get(client)
        x = (
            source.x + source.w * share
            if share is not None
            # The adapters' lane runs down the strip their frame keeps clear of the
            # plugins one, so the arrow passes it instead of crossing it.
            else (frames[PLUGINS].right + source.right) / 2
        )
        return [(x, source.bottom), (x, at.domain.y)], (x + 10, at.domain.y - 14)
    if (client, supplier) == (FRONTENDS, APP):
        y, left = app.mid_y, frames[FRONTENDS].right
        return [(left, y), (app.x, y)], (_centred(left, app.x), y - 10)
    if (client, supplier) == (APP, ENGINE):
        y = app.mid_y
        return [(app.right, y), (engine.x, y)], (_centred(app.right, engine.x), y - 10)
    if (client, supplier) == (FRONTENDS, ENGINE):
        y, left = app.bottom + 40, frames[FRONTENDS].right
        return [(left, y), (engine.x, y)], (_centred(left, engine.x), y - 10)
    if (client, supplier) == (APP, ADAPTERS):
        note_y = MARGIN + 30
        return (
            [
                (app.mid_x, app.y),
                (app.mid_x, note_y),
                (frames[ADAPTERS].mid_x, note_y),
                (frames[ADAPTERS].mid_x, frames[ADAPTERS].y),
            ],
            (app.mid_x + 12, note_y - 10),
        )
    if (client, supplier) == (PLUGINS, ENGINE):
        plugins = frames[PLUGINS]
        y = plugins.bottom + 34
        x = engine.x + engine.w * 0.2
        return (
            [
                (plugins.x + 40, plugins.bottom),
                (plugins.x + 40, y),
                (x, y),
                (x, engine.bottom),
            ],
            (x + 24, y - 10),
        )
    raise SystemExit(
        f"the map has no lane for the import {client} → {supplier}: add one to `_route`"
    )


def _imports(at: Plan) -> list[str]:
    drawn = []
    for client, supplier in sorted(dependencies()):
        points, (label_x, label_y) = _route(at, client, supplier)
        label = COMPOSITION_ROOT if (client, supplier) == (APP, ADAPTERS) else IMPORT
        drawn.append(_path(points, "imports"))
        drawn.append(_text(label_x, label_y, label, "import-label", "start"))
    return drawn


def svg() -> str:
    at = plan()
    bound = bindings()
    label = (
        f"cora as a UML component diagram: {len(frontends())} frontends, an engine of "
        f"{len(at.parts)} parts, {len(bound)} required interfaces wired to the "
        "components that provide them, and the packages each one imports. "
        "Generated by scripts/gen_component_map.py."
    )
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {at.width:g}'
        f' {at.height:g}" width="{at.width:g}" height="{at.height:g}" role="img"'
        f' aria-label="{label}">',
        STYLE.strip("\n"),
        '  <defs><marker id="import" viewBox="0 0 10 10" refX="9" refY="5"'
        ' markerWidth="9" markerHeight="9" orient="auto-start-reverse">'
        '<path d="M 0 1 L 9 5 L 0 9" fill="none" stroke="#8f96a3"'
        ' stroke-width="1.4"/></marker></defs>',
    ]

    for name, frame in at.frames.items():
        out += _frame(frame, name)
    engine = at.boxes[ENGINE]
    out += [
        _rect(engine, "engine", 6.0),
        _text(engine.x + 20, engine.y + 34, ENGINE, "name", "start"),
        *_icon(engine, "glyph-engine"),
    ]
    for role, kind in engine_parts():
        part = at.parts[role]
        out += [
            _rect(part, "part"),
            _text(
                part.x + 16,
                part.mid_y + 5,
                f"{role}: {kind}",
                "part-name role",
                "start",
            ),
        ]
    for page in frontends():
        out += _component(at.boxes[page], page)
    out += _component(at.boxes[APP], APP)
    out += _component(at.domain, DOMAIN)

    modules = declaring_modules()
    for binding in bound:
        for provider in binding.providers:
            out += _component(at.boxes[provider], provider)
    for binding in bound:
        if binding.package == ADAPTERS:
            out += _assembly(at, binding.port, binding.providers[0], modules)
        else:
            out += _plugin_assembly(at, binding.providers, modules)
    out += _imports(at)

    out.append("</svg>")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    MAP.write_text(svg())
    print(f"wrote {MAP.relative_to(ROOT)}")
