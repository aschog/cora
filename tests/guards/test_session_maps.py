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
    """The hash is asked first, so the drawing has both paths the source has, and the
    branch that returns takes the rest of the method as its other operand. Two forks,
    one per `if`: the repair has its own, and a branch that says nothing keeps its place
    in the one it belongs to rather than letting the other side read as unconditional.
    """
    forks = fragments(generator.upload())

    assert [fork.operator for fork in forks] == ["alt", "alt"]
    assert [[guard for guard, _ in fork.operands] for fork in forks] == [
        ["retriever.contains(file_hash)", "else"],
        ["documents.read(file_hash) is not None", "else"],
    ]


def guarded(sequence: generator.Sequence) -> set[str]:
    """Every message that stands inside some fragment, by its label.

    Drawn flat, a message says it always happens. So what a fork can go wrong about is
    not which branches it draws but which messages it leaves outside them.
    """
    found: set[str] = set()

    def walk(lines: tuple[generator.Line, ...], under: bool) -> None:
        for line in lines:
            if isinstance(line, generator.Fragment):
                for _, inner in line.operands:
                    walk(inner, True)
            elif under and isinstance(line, generator.Call):
                found.add(line.label)

    walk(sequence.lines, False)
    return found


def test_a_repair_only_reads_what_was_never_kept() -> None:
    """`_repair` returns early when the text is already there, so the parse and the
    write behind that branch are what the drawing has to put inside a fork: flat, they
    say every duplicate upload re-reads the file and rewrites it.
    """
    kept = "documents.read(file_hash) is not None"
    forks = [
        fork
        for fork in fragments(generator.upload())
        if any(guard == kept for guard, _ in fork.operands)
    ]

    assert forks, "the drawing has no fork on whether the text was already kept"
    said = {
        line.label
        for _, lines in forks[0].operands
        for line in generator.flattened(lines)
        if isinstance(line, generator.Call)
    }
    assert "ingest(data, filename, loaders)" in said
    assert "keep(file_hash, text)" in said


def test_a_paused_turn_is_not_drawn_being_recorded() -> None:
    """`_turn` raises before it records, so recording stands behind the branch that
    found nothing parked. Drawn flat it is the one thing a pause promises not to do."""
    assert "record(thread_id, turn)" in guarded(generator.turn())


def test_the_model_is_drawn_answering() -> None:
    """A reply belongs to the call that was written outermost, which is the one whose
    value the statement binds: `reply = chat_model.complete(_prompt(state), …)` fetches
    the reply from the model, not from the step's own prompt."""
    replies = {
        (line.sender, line.label)
        for line in generator.flattened(generator.round_taken().lines)
        if isinstance(line, generator.Reply)
    }

    assert ("chat_model", "reply") in replies


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
MAP_PAGE = workspace.ROOT / "docs" / "big-picture.md"
# Where a message names the participant itself, it is a call *of* it rather than a
# method *on* it — a step is a `Step`, and its own role is what the graph calls it by.
# `run` is not in the same class: it is the slot a `Tool` is reached through, so it is
# exempt on the one lifeline that is a tool and nowhere else.
CALLED_THROUGH_A_SLOT = {("search", "search_documents"): "run"}


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
            if declared is None:
                continue
            through = CALLED_THROUGH_A_SLOT.get((sequence.name, line.receiver))
            if message == through:
                continue
            if message == line.receiver:
                assert "__call__" in declared, (
                    f"{sequence.name}: {kinds[line.receiver]} is called by its own "
                    "role but is not callable"
                )
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


def test_what_stands_behind_a_port_is_read_and_not_declared() -> None:
    """`assemble` fills `ContextSource` inside itself, so the drawing reads which local
    was handed to the function that offers the tools. Read rather than declared, a
    wrapper put in front of the knowledge base would be drawn instead of it.
    """
    standing = generator.behind()
    promised = _methods("ContextSource")

    assert promised, "cora.ports.context_source declares no ContextSource"
    assert standing["ContextSource"] == "KnowledgeBase"
    assert promised <= (_methods(standing["ContextSource"]) or set())


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


def _labels(path) -> list[tuple[str, float, float]]:  # type: ignore[no-untyped-def]
    """Every message label, with the x it spans from and to."""
    found = []
    for text in ET.parse(path).getroot().iter(f"{SVG}text"):
        styles = set((text.get("class") or "").split())
        if not styles & {"said", "answer"}:
            continue
        span = drawings._wide(text.text or "", 12.5 if "said" in styles else 11.5)
        middle = float(text.get("x") or 0)
        start = middle - span / 2 if text.get("text-anchor") == "middle" else middle
        found.append((text.text or "", start, start + span))
    return found


def test_no_label_is_drawn_off_the_page() -> None:
    """A message an object sends itself is drawn to the right of its own lifeline, so on
    the last lifeline the drawing has to be wider than its columns. Past the edge of the
    viewBox a label is not narrow or ugly — it is simply not shown.
    """
    for path in drawings.written():
        root = ET.parse(path).getroot()
        edge = float((root.get("viewBox") or "0 0 0 0").split()[2])
        for label, start, end in _labels(path):
            assert start >= -1 and end <= edge + 1, (
                f"{path.name}: '{label}' is drawn outside the page"
            )


def test_a_label_that_flies_over_a_lifeline_is_read_on_its_own_ground() -> None:
    """Otherwise the lifeline is a dashed line struck through the middle of a word."""
    for path in drawings.written():
        root = ET.parse(path).getroot()
        lifelines = {
            round(float(line.get("d", "M 0 0").split()[1]), 1)
            for line in root.iter(f"{SVG}path")
            if "life" in (line.get("class") or "").split()
        }
        grounds = [
            (
                float(one.get("x") or 0),
                float(one.get("x") or 0) + float(one.get("width") or 0),
            )
            for one in root.iter(f"{SVG}rect")
            if "sheet" in (one.get("class") or "").split()
        ]
        for label, start, end in _labels(path):
            crossed = [one for one in lifelines if start < one < end]
            if not crossed:
                continue
            assert any(left <= start and end <= right for left, right in grounds), (
                f"{path.name}: '{label}' is struck through by a lifeline"
            )


def test_the_page_shows_every_drawing_and_no_page_draws_by_hand() -> None:
    """Nothing renders a fence any more — the extension that turned one into a diagram
    went with the drawings it used to draw, so a fence added to either narrative page
    would render as a block of text where a picture was meant.
    """
    page = PAGE.read_text()

    for path in drawings.written():
        assert f"assets/{path.name}" in page, f"happy-path.md does not show {path.name}"
    for written in (PAGE, MAP_PAGE):
        assert "```mermaid" not in written.read_text(), (
            f"{written.name} draws by hand, and nothing on this site renders a fence"
        )


def test_every_drawing_is_valid_xml_naming_what_it_shows() -> None:
    for path in drawings.written():
        root = ET.parse(path).getroot()

        assert (root.get("aria-label") or "").startswith("A UML sequence diagram")
        heads = [
            rect
            for rect in root.iter(f"{SVG}rect")
            if "head" in (rect.get("class") or "").split()
        ]
        drawn = drawings.DRAWINGS[path.name]()
        assert len(heads) == len(drawn.lifelines), (
            f"{path.name} draws {len(heads)} participants for "
            f"{len(drawn.lifelines)} lifelines"
        )
