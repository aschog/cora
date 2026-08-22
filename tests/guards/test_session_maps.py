"""The session drawings, checked against the code they are read out of.

What they can go wrong about is the code moving underneath them — a call added to a
method, a branch added to one, a method renamed — so every check reads the source and
asks the drawing for the same thing.
"""

import ast
import xml.etree.ElementTree as ET

import gen_session_maps as drawings
import sequences as generator
import workspace


def messages(sequence: generator.Sequence) -> list[tuple[str, str, str]]:
    """Every call the sequence carries, fragments opened out, in order."""
    return [
        (line.sender, line.receiver, line.label)
        for line in generator.flattened(sequence.lines)
        if isinstance(line, generator.Call)
    ]


def fragments(sequence: generator.Sequence) -> list[generator.Fragment]:
    return [
        line
        for line in generator.flattened(sequence.lines)
        if isinstance(line, generator.Fragment)
    ]


def test_the_upload_sequence_is_the_calls_add_file_makes_in_order() -> None:
    assert messages(generator.upload()) == [
        ("cora.frontends", "knowledge_base", "add_file(data, filename)"),
        ("knowledge_base", "retriever", "contains(file_hash)"),
        ("knowledge_base", "knowledge_base", "_repair(data, filename, file_hash)"),
        ("knowledge_base", "documents", "read(file_hash)"),
        ("knowledge_base", "ingest", "ingest(data, filename, loaders)"),
        ("knowledge_base", "documents", "keep(file_hash, text)"),
        ("knowledge_base", "ingest", "ingest(data, filename, loaders)"),
        ("knowledge_base", "embedder", "embed([chunk.text for chunk in chunks])"),
        ("knowledge_base", "documents", "keep(file_hash, text)"),
        ("knowledge_base", "retriever", "add(chunks, vectors, file_hash)"),
    ]


def test_the_upload_sequence_branches_where_the_method_does() -> None:
    """The hash is asked first, so the drawing has both paths the source has — and the
    branch that returns takes the rest of the method as its other operand. One fork,
    because the repair's own is a guard clause: nothing is said on it.
    """
    [fork] = fragments(generator.upload())

    assert fork.operator == "alt"
    assert [guard for guard, _ in fork.operands] == [
        "retriever.contains(file_hash)",
        "else",
    ]


def test_a_lifeline_is_named_for_the_field_and_what_really_fills_it() -> None:
    """A participant is a field of the class being read, drawn `role: Type` — and the
    type is not the annotation but whatever the composition root puts behind it, because
    a sequence is one run of the app and a run has one adapter per port.
    """
    drawn = {line.role: line.kind for line in generator.upload().lifelines}

    assert drawn["retriever"] == "ChromaRetriever"
    assert drawn["embedder"] == "SentenceTransformerEmbedder"
    assert drawn["documents"] == "SqliteDocuments"


def test_the_caller_is_the_package_every_call_site_shares() -> None:
    """Both frontends upload, so naming either one would be drawing half the callers."""
    assert generator.callers_of("add_file", generator.KNOWLEDGE) == "cora.frontends"


def test_the_search_drawing_opens_the_class_the_tool_is_built_around() -> None:
    """`search_documents` is a name in a schema and `DocumentSearch` is what answers to
    it: the drawing's claim that one runs the other is the `Tool` the module builds."""
    assert generator.tool_built_in(generator.RETRIEVAL) == (
        "search_documents",
        "DocumentSearch",
    )


def test_the_search_sequence_reaches_the_index_through_the_knowledge_base() -> None:
    assert messages(generator.search()) == [
        ("tool_runtime", "search_documents", "run(**arguments)"),
        ("search_documents", "context_source", "search(query, top_k)"),
        ("context_source", "embedder", "embed([query])"),
        ("context_source", "retriever", "query(query_vector, k)"),
    ]


def test_a_value_the_step_makes_is_no_participant() -> None:
    """`CitableHits(…)` is the payload being built, not something a message is sent to:
    a lifeline for it would put a domain value among the objects of a run."""
    assert "CitableHits" not in {line.role for line in generator.search().lifelines}


def test_a_reply_is_what_the_interface_says_it_answers_with() -> None:
    """Nothing binds a value that is returned or tested, so the drawing reads the reply
    off the signature — the promise, rather than a name the body happened to use."""
    replies = [
        (line.sender, line.label)
        for line in generator.flattened(generator.search().lines)
        if isinstance(line, generator.Reply)
    ]

    assert ("retriever", "list[RetrievedChunk]") in replies
    assert ("search_documents", "CitableHits") in replies


SVG = "{http://www.w3.org/2000/svg}"
PAGE = workspace.ROOT / "docs" / "happy-path.md"
# A message whose name is the participant's own is a call *of* it rather than a method
# *on* it: a step is a `Step`, a tool is reached through the `run` slot that holds it.
CALLED_AS_ITSELF = ("run", "__call__")


def _methods(kind: str) -> set[str] | None:
    """Every method a drawn class declares, or nothing where no class is drawn."""
    for path in sorted((workspace.ROOT / "src" / "cora").rglob("*.py")):
        for node in ast.parse(path.read_text()).body:
            if isinstance(node, ast.ClassDef) and node.name == kind:
                return {
                    one.name
                    for one in node.body
                    if isinstance(one, ast.FunctionDef | ast.AsyncFunctionDef)
                }
    return None


def sequences() -> list[generator.Sequence]:
    return [read_it() for read_it in drawings.DRAWINGS.values()]


def test_every_message_names_a_method_the_receiver_really_has() -> None:
    """The one thing a drawing read off one class cannot check for itself: the class at
    the other end of the arrow. A method renamed there leaves a drawing that names
    something nobody answers to.
    """
    for sequence in sequences():
        kinds = {line.role: line.kind for line in sequence.lifelines}
        for line in generator.flattened(sequence.lines):
            if not isinstance(line, generator.Call):
                continue
            message = line.label.split("(")[0]
            declared = _methods(kinds.get(line.receiver, ""))
            if declared is None or message in (line.receiver, *CALLED_AS_ITSELF):
                continue
            assert message in declared, (
                f"{sequence.name}: {kinds[line.receiver]} has no {message}"
            )


def test_the_round_draws_every_node_and_every_route_the_graph_declares() -> None:
    """The shape of a turn is the runner's own statement of it, so a node added to the
    graph and left out of the drawing is a step the page denies happens."""
    plan = generator.routing()
    drawn = {line.role for line in generator.round_taken().lifelines}
    guards = {
        guard
        for line in generator.flattened(generator.round_taken().lines)
        if isinstance(line, generator.Fragment)
        for guard, _ in line.operands
    }

    assert set(plan.nodes.values()) <= drawn
    assert {route for route, _ in plan.routes} <= guards


def test_the_knowledge_base_is_still_what_stands_behind_the_search_tool() -> None:
    """The one binding the drawing is told rather than reads: `assemble` hands the
    knowledge base down two calls before it arrives as a `ContextSource`."""
    behind = generator.BEHIND["ContextSource"]
    promised = _methods("ContextSource") or set()

    assert promised <= (_methods(behind) or set())


def test_a_tool_is_run_in_one_place_only() -> None:
    """Which is why the search drawing may name the runtime as what opens it: nothing
    else in cora calls what a `Tool` holds."""
    runs = {
        generator._dotted(path)
        for path in generator._sources()
        for node in generator._ordered(ast.parse(path.read_text()))
        if isinstance(node.func, ast.Attribute)
        and node.func.attr == "run"
        and generator._argument(node.func.value) == "tool"
    }

    assert runs == {"cora.engine.tool_runtime"}


def test_the_committed_drawings_are_what_the_generator_writes_today() -> None:
    for path, drawing in drawings.written().items():
        assert path.read_text() == drawing, (
            f"{path.name} is behind the source it is drawn from: run `make diagram`"
        )


def test_every_drawing_takes_its_colours_from_the_reader() -> None:
    """An `<img>`-embedded SVG inherits nothing from the page it is pasted into, so each
    one carries its own dark block and paints no sheet of its own."""
    for path in drawings.written():
        page = path.read_text()

        assert "prefers-color-scheme: dark" in page
        assert 'fill="white"' not in page


def test_the_page_shows_every_drawing_and_draws_nothing_by_hand() -> None:
    page = PAGE.read_text()

    for path in drawings.written():
        assert f"assets/{path.name}" in page, f"happy-path.md does not show {path.name}"
    assert "```mermaid" not in page, "the page's pictures are generated from the source"


def test_every_drawing_is_valid_xml_naming_what_it_shows() -> None:
    for path in drawings.written():
        root = ET.parse(path).getroot()

        assert (root.get("aria-label") or "").startswith("A UML sequence diagram")
        assert root.iter(f"{SVG}rect")
