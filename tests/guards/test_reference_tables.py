"""The hand-written reference tables, checked against what they are about.

The drawings on this site cannot go stale, because a generator writes them and a guard
pins them. These two tables are the opposite: prose a person keeps, stating facts the
source states as well — every route the page serves, and every port the engine talks
through. So they get the same treatment the drawings do.
"""

import ast
import re

import gen_component_map as components
import workspace

REFERENCE = workspace.ROOT / "docs" / "reference"
API = (
    workspace.ROOT
    / "frontends"
    / "react"
    / "src"
    / "cora"
    / "frontends"
    / "react"
    / "api.py"
)
PORTS = workspace.ROOT / "src" / "cora" / "ports"
ROUTE_ROW = re.compile(r"^\| `(/[^`]+)` \| `([A-Z]+)` \|", re.MULTILINE)
PORT_ROW = re.compile(r"^\| \*\*(\w+)\*\* \|", re.MULTILINE)
SPELLED = {8: "eight", 9: "nine", 10: "ten", 11: "eleven", 12: "twelve"}


def served() -> set[tuple[str, str]]:
    """Every route the shell mounts, off the routing table it is built with."""
    return {
        (path.value, method.value)
        for node in ast.walk(ast.parse(API.read_text()))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "Route"
        and isinstance(path := node.args[0], ast.Constant)
        and isinstance(path.value, str)
        for keyword in node.keywords
        if keyword.arg == "methods" and isinstance(keyword.value, ast.List)
        for method in keyword.value.elts
        if isinstance(method, ast.Constant) and isinstance(method.value, str)
    }


def declared_names() -> set[str]:
    """Every name `cora.ports` declares — a Protocol, or an alias for a callable one."""
    found = set()
    for path in sorted(PORTS.glob("*.py")):
        for node in ast.parse(path.read_text()).body:
            if isinstance(node, ast.ClassDef):
                found.add(node.name)
            elif isinstance(node, ast.AnnAssign | ast.Assign):
                targets = (
                    [node.target] if isinstance(node, ast.AnnAssign) else node.targets
                )
                found |= {one.id for one in targets if isinstance(one, ast.Name)}
    return found


def test_the_route_table_is_the_routes_the_shell_mounts() -> None:
    """A route added without a row is a page the reader cannot find, and a row without a
    route is a request that answers 404 to whoever trusted the table."""
    tabled = set(ROUTE_ROW.findall((REFERENCE / "http-api.md").read_text()))

    assert tabled == served()


def test_the_port_table_has_a_row_per_port_the_engine_talks_through() -> None:
    """The count is the page's own claim — a tenth port would otherwise arrive with the
    sentence above the table still saying nine."""
    page = (REFERENCE / "ports.md").read_text()
    tabled = set(PORT_ROW.findall(page))
    bound = {binding.port for binding in components.bindings()}

    assert tabled <= declared_names(), "the table names something `cora.ports` does not"
    assert len(tabled) == len(bound)
    assert f"The {SPELLED[len(bound)]} ports" in page
