import pathlib

import grimp
from grimp import ImportGraph

import package_diagram
import workspace

PAGE = (
    pathlib.Path(__file__).resolve().parent.parent / "docs" / "diagrams" / "packages.md"
)


def _graph(*modules: str, imports: tuple[tuple[str, str], ...] = ()) -> ImportGraph:
    graph = ImportGraph()
    for module in modules:
        graph.add_module(module)
    for importer, imported in imports:
        graph.add_import(importer=importer, imported=imported)
    return graph


def _committed_block(page: str) -> str:
    _, _, rest = page.partition("```mermaid\n")
    block, _, _ = rest.partition("```")
    return block.strip()


def test_the_committed_diagram_is_the_one_the_workspace_produces() -> None:
    assert _committed_block(PAGE.read_text()) == package_diagram.render()


def test_a_box_is_a_layer_of_the_namespace() -> None:
    graph = _graph("cora", "cora.domain", "cora.domain.chunk", "cora.engine")
    assert package_diagram.boxes(graph) == ("cora.domain", "cora.engine")


def test_the_namespace_root_is_no_box() -> None:
    assert package_diagram.boxes(_graph("cora")) == ()


def test_an_extension_point_contributes_its_children_rather_than_itself() -> None:
    graph = _graph(
        "cora",
        "cora.plugins",
        "cora.plugins.fitness",
        "cora.plugins.fitness.tools",
        "cora.frontends",
        "cora.frontends.streamlit",
    )
    assert package_diagram.boxes(graph) == (
        "cora.frontends.streamlit",
        "cora.plugins.fitness",
    )


def test_a_second_frontend_is_a_box_with_no_edit_here() -> None:
    graph = _graph(
        "cora", "cora.frontends", "cora.frontends.streamlit", "cora.frontends.cli"
    )
    assert package_diagram.boxes(graph) == (
        "cora.frontends.cli",
        "cora.frontends.streamlit",
    )


def test_several_modules_crossing_one_boundary_are_one_arrow() -> None:
    graph = _graph(
        "cora",
        "cora.engine",
        "cora.engine.agent",
        "cora.engine.steps",
        "cora.domain",
        "cora.domain.trace",
        imports=(
            ("cora.engine.agent", "cora.domain.trace"),
            ("cora.engine.steps", "cora.domain.trace"),
        ),
    )
    assert package_diagram.dependencies(graph) == (("cora.engine", "cora.domain"),)


def test_a_packages_own_imports_are_no_arrow_to_itself() -> None:
    graph = _graph(
        "cora",
        "cora.domain",
        "cora.domain.citations",
        "cora.domain.prose",
        imports=(("cora.domain.citations", "cora.domain.prose"),),
    )
    assert package_diagram.dependencies(graph) == ()


def test_a_mutual_pair_is_drawn_both_ways() -> None:
    graph = _graph(
        "cora",
        "cora.domain",
        "cora.domain.agent_state",
        "cora.ports",
        "cora.ports.graph",
        imports=(
            ("cora.domain.agent_state", "cora.ports.graph"),
            ("cora.ports.graph", "cora.domain.agent_state"),
        ),
    )
    assert package_diagram.dependencies(graph) == (
        ("cora.domain", "cora.ports"),
        ("cora.ports", "cora.domain"),
    )


def test_a_framework_is_no_box_and_no_arrow() -> None:
    graph = _graph(
        "cora",
        "cora.adapters",
        "cora.adapters.chroma_retriever",
        "chromadb",
        imports=(("cora.adapters.chroma_retriever", "chromadb"),),
    )
    assert package_diagram.boxes(graph) == ("cora.adapters",)
    assert package_diagram.dependencies(graph) == ()


def test_two_boxes_sharing_a_leaf_name_stay_two_boxes() -> None:
    """The trap pyreverse's own Mermaid output falls into: a node named by its leaf
    merges two packages into one."""
    graph = _graph(
        "cora",
        "cora.plugins",
        "cora.plugins.security",
        "cora.frontends",
        "cora.frontends.security",
    )
    block = package_diagram.diagram(graph)
    assert "cora.plugins.security" in block
    assert "cora.frontends.security" in block


def test_a_box_nothing_imports_and_that_imports_nothing_is_still_drawn() -> None:
    graph = _graph("cora", "cora.engine", "cora.engine.agent")
    assert package_diagram.diagram(graph).splitlines()[-1] == "  cora.engine"


def test_the_app_declares_the_guard_and_imports_it_nowhere() -> None:
    """The arrow the distributions diagram in big-picture.md has and this one must not:
    `cora` ships the plugin its default set names without depending on its code."""
    member = next(
        member
        for member in workspace.members()
        if workspace.distribution(member) == "cora"
    )
    declared = workspace.manifest(member)["project"]["dependencies"]
    assert any(name.startswith("cora-plugin-security") for name in declared)
    crossings = package_diagram.dependencies(grimp.build_graph(package_diagram.ROOT))
    assert ("cora.app", "cora.plugins.security") not in crossings


def test_the_command_rewrites_the_block_and_leaves_the_prose(
    tmp_path: pathlib.Path,
) -> None:
    page = tmp_path / "packages.md"
    page.write_text(
        "# Title\n\nprose above\n\n"
        "```mermaid\nflowchart BT\n  stale\n```\n\n"
        "prose below\n"
    )
    package_diagram.write(page)
    written = page.read_text()
    assert _committed_block(written) == package_diagram.render()
    assert written.startswith("# Title\n\nprose above\n")
    assert written.endswith("```\n\nprose below\n")
