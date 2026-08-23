"""Reading a module the way every generator here has to read one.

Five questions asked by both drawings — what a file parses to, which function is which,
what a name was imported from, what a call calls, and what a body bound to a local. They
are about source rather than about either drawing, so they live where neither owns them:
`gen_component_map` cannot rename one out from under `sequences`, and a third generator
asks the same questions of the same names.
"""

import ast
from pathlib import Path


def parsed(path: Path) -> ast.Module:
    return ast.parse(path.read_text())


def function(tree: ast.Module, name: str) -> ast.FunctionDef:
    """The named function of a module.

    Raises:
        StopIteration: The module declares no function by that name.
    """
    return next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    )


def imported(tree: ast.Module) -> dict[str, str]:
    """Every name a module took from somewhere, and where it took it from."""
    return {
        alias.asname or alias.name: node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }


def called(node: ast.expr) -> str | None:
    """What an expression calls — past a `partial`, and past an attribute on what it
    returned."""
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            if node.func.id == "partial" and node.args:
                return called(node.args[0])
            return node.func.id
        if isinstance(node.func, ast.Attribute) and isinstance(
            node.func.value, ast.Name
        ):
            return node.func.value.id
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return called(node.value)
    return None


def bound(body: ast.FunctionDef) -> dict[str, str]:
    """Each local a function assigns, and what was called to make it."""
    found = {}
    for node in ast.walk(body):
        if (
            isinstance(node, ast.Assign)
            and isinstance(node.targets[0], ast.Name)
            and (filled := called(node.value))
        ):
            found[node.targets[0].id] = filled
    return found
