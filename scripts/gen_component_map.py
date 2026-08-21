import ast
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).parent.parent
ASSEMBLY = ROOT / "src" / "cora" / "app" / "assembly.py"
PORTS = ROOT / "src" / "cora" / "ports"
LOADERS = ROOT / "src" / "cora" / "adapters" / "loaders.py"
MAP = ROOT / "docs" / "assets" / "component-map.svg"

# `assemble` takes the factory; the engine holds the runner it returns, and that is the
# port a reader of the map is looking for.
AS_DRAWN = {"GraphFor": "GraphRunner"}
# Two slots the engine talks through that are not arguments to `assemble`: the loader
# registry is fixed at the composition root, and a plugin arrives in the plugin set.
BESIDE_THE_SIGNATURE = ("Loader", "Plugin")


@dataclass(frozen=True)
class Binding:
    port: str
    adapters: tuple[str, ...]


def _module(tree: ast.Module) -> dict[str, str]:
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
        for node in ast.parse(path.read_text()).body
        if isinstance(node, ast.ClassDef)
        and any(
            isinstance(base, ast.Name) and base.id == "Protocol" for base in node.bases
        )
    }


def declared_ports() -> set[str]:
    return {name for path in PORTS.glob("*.py") for name in _protocols(path)}


def _named(annotation: ast.expr | None) -> set[str]:
    return (
        {node.id for node in ast.walk(annotation) if isinstance(node, ast.Name)}
        if (annotation)
        else set()
    )


def _slots(tree: ast.Module) -> list[tuple[str, str]]:
    """Each keyword-only slot of `assemble` that names a port, in signature order."""
    ports = declared_ports()
    found = []
    for argument in _function(tree, "assemble").args.kwonlyargs:
        for name in sorted(_named(argument.annotation)):
            drawn = AS_DRAWN.get(name, name)
            if name in ports or drawn in ports:
                found.append((argument.arg, drawn))
    return found


def _called(node: ast.expr) -> str | None:
    """The class or function a slot is filled with, however the call is written."""
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            # `partial(langgraph_for, …)` binds the factory, not the partial.
            if node.func.id == "partial" and node.args:
                return _called(node.args[0])
            return node.func.id
        if isinstance(node.func, ast.Attribute) and isinstance(
            node.func.value, ast.Name
        ):
            return node.func.value.id
    if isinstance(node, ast.Name):
        return node.id
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
    made, `LangGraphRunner` is what stands behind the port.
    """
    module = imported.get(name, "")
    if not module.startswith("cora."):
        return name
    source = ROOT.joinpath("src", *module.split(".")).with_suffix(".py")
    if not source.exists():
        return name
    made = [
        returned
        for node in ast.parse(source.read_text()).body
        if isinstance(node, ast.FunctionDef) and node.name == name
        for statement in ast.walk(node)
        if isinstance(statement, ast.Return) and statement.value is not None
        for returned in (_called(statement.value),)
        if returned
    ]
    return made[0] if made else name


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
    imported = _module(tree)
    filled = {}
    for keyword in call.keywords:
        if keyword.arg and (name := _called(keyword.value)):
            filled[keyword.arg] = _provider(resolved.get(name, name), imported)
    return filled


def _loaders() -> tuple[str, ...]:
    registry = next(
        node
        for node in ast.parse(LOADERS.read_text()).body
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.target.id == "LOADERS"
    )
    assert isinstance(registry.value, ast.Dict)
    named = [value.id for value in registry.value.values if isinstance(value, ast.Name)]
    return tuple(dict.fromkeys(named))


def _packages(directory: str) -> tuple[str, ...]:
    return tuple(
        sorted(path.name for path in (ROOT / directory).iterdir() if path.is_dir())
    )


def bindings() -> tuple[Binding, ...]:
    tree = ast.parse(ASSEMBLY.read_text())
    filled = _assembled(tree)
    bound = [
        Binding(port, (filled[slot],)) for slot, port in _slots(tree) if slot in filled
    ]
    beside = {
        "Loader": _loaders(),
        "Plugin": tuple(f"cora.plugins.{name}" for name in _packages("plugins")),
    }
    return tuple(bound) + tuple(
        Binding(port, beside[port]) for port in BESIDE_THE_SIGNATURE
    )


def engine_parts() -> tuple[str, ...]:
    """What `assemble` always builds, in the order it reads. The debug wrappers are not
    here because they are not always there: they stand behind an `if`, around a port."""
    tree = ast.parse(ASSEMBLY.read_text())
    imported = _module(tree)
    always = [
        node
        for statement in _function(tree, "assemble").body
        if not isinstance(statement, ast.If)
        for node in ast.walk(statement)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and imported.get(node.func.id, "").startswith("cora.engine")
    ]
    named = [
        node.func.id
        for node in sorted(always, key=lambda call: (call.lineno, call.col_offset))
        if isinstance(node.func, ast.Name)
    ]
    return tuple(dict.fromkeys(named))


def frontends() -> tuple[str, ...]:
    return _packages("frontends")


DOMAIN = "cora.domain"
SPEAKERS = {
    "engine": ("src", "cora", "engine"),
    "outward": ("src", "cora", "adapters"),
    "frontends": ("frontends",),
    "plugins": ("plugins",),
}


def speaks_domain() -> frozenset[str]:
    """Which drawn groups import the domain. Everything cora has speaks in its value
    objects and its errors, and the drawing should say so rather than imply a layer."""
    found = set()
    for group, parts in SPEAKERS.items():
        for module in ROOT.joinpath(*parts).rglob("*.py"):
            if f"from {DOMAIN}" in module.read_text():
                found.add(group)
                break
    return frozenset(found)


STYLE = """
  <style>
    text { font: 13px/1.4 -apple-system, "Segoe UI", Roboto, sans-serif; fill: #202124 }
    .stereotype { font-size: 10.5px; fill: #5f6368; letter-spacing: .04em }
    .name { font-weight: 600 }
    .engine { fill: #f6f4ff; stroke: #6c5ce7; stroke-width: 1.8 }
    .part { fill: #ffffff; stroke: #6c5ce7; stroke-width: 1.2 }
    .part-name { fill: #4b3fbb; font-weight: 600 }
    .outer { fill: #ffffff; stroke: #9aa0a6; stroke-width: 1.4 }
    .wire { stroke: #9aa0a6; stroke-width: 1.3; fill: none }
    .socket { stroke: #9aa0a6; stroke-width: 1.6; fill: none }
    .ball { fill: #ffffff; stroke: #9aa0a6; stroke-width: 1.6 }
    /* The two labels that stand on the page itself, not on a box: one mid-tone that
       reads on either background, because the page's scheme is the site's to choose
       and this file only sees the reader's system. */
    .port { fill: #6b7280; font-size: 12px }
    .drives { stroke: #e8710a; stroke-width: 1.4; fill: none;
              stroke-dasharray: 5 4; marker-end: url(#arrow) }
    .uses { stroke: #9aa0a6; stroke-width: 1.3; fill: none;
            stroke-dasharray: 5 4; marker-end: url(#uses) }
    .drives-label { fill: #d97706; font-size: 12px }
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

ROW = 70
BOX = 56
PART = 46
ENGINE_X, ENGINE_W = 352.0, 300.0
OUTER_W = 268.0
ADAPTER_X = 892.0
FRONTEND_X, FRONTEND_W = 16.0, 200.0
DOMAIN_GAP = 60.0


def _text(x: float, y: float, value: str, style: str, anchor: str = "middle") -> str:
    return (
        f'  <text x="{x:g}" y="{y:g}" class="{style}" text-anchor="{anchor}">'
        f"{value}</text>"
    )


def _component(x: float, y: float, width: float, name: str, height: float = BOX) -> str:
    return "\n".join(
        (
            f'  <rect x="{x:g}" y="{y:g}" width="{width:g}" height="{height:g}"'
            ' rx="4" class="outer"/>',
            _text(x + width / 2, y + 22, "«component»", "stereotype"),
            _text(x + width / 2, y + 40, name, "name"),
        )
    )


def _socket(x: float, y: float, port: str, wire_from: float, wire_to: float) -> str:
    """The engine's required interface cupping the adapter's provided one."""
    return "\n".join(
        (
            f'  <path d="M {wire_from:g} {y:g} H {x - 13:g}" class="wire"/>',
            f'  <path d="M {x - 13:g} {y - 11:g} A 11 11 0 0 0 {x - 13:g} {y + 11:g}"'
            ' class="socket"/>',
            f'  <circle cx="{x + 4:g}" cy="{y:g}" r="5.5" class="ball"/>',
            f'  <path d="M {x + 9.5:g} {y:g} H {wire_to:g}" class="wire"/>',
            _text((wire_from + wire_to) / 2, y - 12, port, "port"),
        )
    )


def svg() -> str:
    bound = bindings()
    parts = engine_parts()
    pages = frontends()
    # The engine spans the ports it binds: a connector that left its side to reach a row
    # below the box would draw a port the engine does not have.
    speakers = speaks_domain()
    height = len(bound) * ROW + 40 + DOMAIN_GAP + BOX
    engine_y, engine_h = 20.0, len(bound) * ROW - ROW + BOX
    domain_y = engine_y + engine_h + DOMAIN_GAP
    rails = engine_y + engine_h / 2
    pitch = (engine_h - 66) / len(parts)
    label = (
        f"cora as components: {len(pages)} frontends drive the engine, "
        f"and its {len(bound)} ports bind one adapter each; every component speaks "
        f"cora.domain. Generated by "
        "scripts/gen_component_map.py."
    )
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1180 {height:g}"'
        f' width="1180" height="{height:g}" role="img" aria-label="{label}">',
        STYLE.strip("\n"),
        '  <defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5"'
        ' markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        '<path d="M 0 1 L 9 5 L 0 9 z" fill="#e8710a"/></marker>'
        '<marker id="uses" viewBox="0 0 10 10" refX="9" refY="5"'
        ' markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        '<path d="M 0 1 L 9 5 L 0 9 z" fill="#9aa0a6"/></marker></defs>',
        f'  <rect x="{ENGINE_X:g}" y="{engine_y:g}" width="{ENGINE_W:g}"'
        f' height="{engine_h:g}" rx="8" class="engine"/>',
        _text(ENGINE_X + ENGINE_W / 2, engine_y + 26, "«component»", "stereotype"),
        _text(ENGINE_X + ENGINE_W / 2, engine_y + 46, "cora.engine", "name"),
    ]

    for index, part in enumerate(parts):
        top = engine_y + 60 + index * pitch
        out += [
            f'  <rect x="{ENGINE_X + 24:g}" y="{top:g}" width="{ENGINE_W - 48:g}"'
            f' height="{pitch - 12:g}" rx="4" class="part"/>',
            _text(ENGINE_X + ENGINE_W / 2, top + pitch / 2 - 2, part, "part-name"),
        ]

    for index, page in enumerate(pages):
        top = rails - len(pages) * (BOX + 14) / 2 + index * (BOX + 14)
        out.append(_component(FRONTEND_X, top, FRONTEND_W, f"cora.frontends.{page}"))
    spine = FRONTEND_X + FRONTEND_W + 42
    out += [
        f'  <path d="M {FRONTEND_X + FRONTEND_W:g} {rails - (BOX + 14) / 2:g}'
        f" H {spine:g} V {rails + (BOX + 14) / 2:g}"
        f' H {FRONTEND_X + FRONTEND_W:g}" class="wire"/>',
        f'  <path d="M {spine:g} {rails:g} H {ENGINE_X:g}" class="drives"/>',
        _text((spine + ENGINE_X) / 2, rails - 12, "App", "drives-label"),
    ]

    for index, binding in enumerate(bound):
        middle = 20 + index * ROW + BOX / 2
        out.append(
            _socket(
                (ENGINE_X + ENGINE_W + ADAPTER_X) / 2,
                middle,
                binding.port,
                ENGINE_X + ENGINE_W,
                ADAPTER_X,
            )
        )
        stacked = len(binding.adapters)
        each = (BOX - 6 * (stacked - 1)) / stacked
        for offset, adapter in enumerate(binding.adapters):
            top = 20 + index * ROW + offset * (each + 6)
            if stacked == 1:
                out.append(_component(ADAPTER_X, top, OUTER_W, adapter))
            else:
                out += [
                    f'  <rect x="{ADAPTER_X:g}" y="{top:g}" width="{OUTER_W:g}"'
                    f' height="{each:g}" rx="4" class="outer"/>',
                    _text(ADAPTER_X + OUTER_W / 2, top + each / 2 + 4, adapter, "name"),
                ]
    out.append(_component(ENGINE_X, domain_y, ENGINE_W, DOMAIN))
    middle = domain_y + BOX / 2
    if "engine" in speakers:
        out.append(
            f'  <path d="M {ENGINE_X + ENGINE_W / 2:g} {engine_y + engine_h:g}'
            f' V {domain_y:g}" class="uses"/>'
        )
    if "frontends" in speakers:
        out.append(
            f'  <path d="M {spine:g} {rails + (BOX + 14) / 2:g} V {middle:g}'
            f' H {ENGINE_X:g}" class="uses"/>'
        )
    if speakers & {"outward", "plugins"}:
        column = ADAPTER_X + OUTER_W / 2
        out.append(
            f'  <path d="M {column:g} {domain_y - DOMAIN_GAP + 6:g} V {middle:g}'
            f' H {ENGINE_X + ENGINE_W:g}" class="uses"/>'
        )
    out.append("</svg>")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    MAP.write_text(svg())
    print(f"wrote {MAP.relative_to(ROOT)}")
