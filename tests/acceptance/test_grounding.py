import pytest

from app_builder import assembled, indexed
from cora.app.assembly import App
from cora.domain.errors import LlmError, RetrievalError, ToolLoopLimitError
from cora.domain.trace import Reconsidered, SecondLookLost, ToolUse
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME
from cora.ports.chat_model import ChatModel, Message, ModelReply
from cora.ports.plugin import Tool, ToolCall
from cora.ports.retrieval import Retriever
from fakes import CountingRetriever, ScriptedChatModel
from fixture_plugins import make_plugin

SEED_DOC = ("protein.md", b"aim for 1.6 g of protein per kg")
OFF_THE_CUFF = "Beginners should train three times a week."
GROUNDED = "Your notes say 1.6 g per kg [1]."
SCOPE = "training and nutrition"
FABRICATED = "Protein is 1.6 g per kg [1]."
THREAD = "t1"


def _app(
    chat_model: ChatModel,
    retriever: Retriever | None = None,
    *,
    scope: str = SCOPE,
    max_tool_rounds: int = 8,
) -> App:
    return indexed(
        assembled(
            chat_model=chat_model,
            retriever=retriever or CountingRetriever(),
            plugin=make_plugin(scope=scope),
            max_tool_rounds=max_tool_rounds,
        ),
        SEED_DOC,
    )


def _searching() -> ModelReply:
    return ModelReply(
        tool_calls=(
            ToolCall(
                name=SEARCH_TOOL_NAME, arguments={"query": "protein"}, call_id="c1"
            ),
        )
    )


@pytest.mark.integration
def test_an_answer_that_skipped_the_documents_is_sent_back_for_them() -> None:
    """One search, and the gate runs it: the model is handed the passages rather
    than asked to fetch them, so the grounded answer costs one round, not three."""
    retriever = CountingRetriever()
    app = _app(
        ScriptedChatModel([ModelReply(text=OFF_THE_CUFF), ModelReply(text=GROUNDED)]),
        retriever,
    )

    result = app.agent.answer("How much protein should I eat?", THREAD)

    assert result.answer == GROUNDED
    assert [source.name for source in result.sources] == ["protein.md"]
    assert retriever.queries == 1


@pytest.mark.integration
def test_the_trace_shows_the_answer_being_sent_back() -> None:
    app = _app(
        ScriptedChatModel(
            [ModelReply(text=OFF_THE_CUFF), _searching(), ModelReply(text=GROUNDED)]
        )
    )

    result = app.agent.answer("How much protein should I eat?", THREAD)

    kinds = [type(step) for step in result.trace]
    assert Reconsidered in kinds
    assert kinds.index(Reconsidered) < kinds.index(ToolUse)


@pytest.mark.integration
def test_small_talk_keeps_its_answer_and_cites_nothing() -> None:
    """The gate looks for every ungrounded answer, small talk included — what it must
    not do is put a citation on a greeting. Irrelevant evidence leaves the answer as
    it was, so nothing is registered against it."""
    retriever = CountingRetriever()
    app = _app(
        ScriptedChatModel([ModelReply(text="Hello!"), ModelReply(text="Hello!")]),
        retriever,
    )

    result = app.agent.answer("Hi there!", THREAD)

    assert result.answer == "Hello!"
    assert result.sources == ()


class _DiesAfterTheNudge:
    """Answers, then fails the round the gate asks for."""

    def __init__(self) -> None:
        self.completions = 0

    def complete(
        self, messages: tuple[Message, ...], tools: tuple[Tool, ...]
    ) -> ModelReply:
        self.completions += 1
        if self.completions == 1:
            return ModelReply(text=OFF_THE_CUFF)
        raise LlmError


class _DiesAfterSearching:
    """Answers, searches when told to, then dies with the documents in hand."""

    def __init__(self) -> None:
        self.completions = 0

    def complete(
        self, messages: tuple[Message, ...], tools: tuple[Tool, ...]
    ) -> ModelReply:
        self.completions += 1
        if self.completions == 1:
            return ModelReply(text=FABRICATED)
        if self.completions == 2:
            return _searching()
        raise LlmError


@pytest.mark.integration
def test_a_dead_second_look_gives_back_the_answer_it_was_second_guessing() -> None:
    app = _app(_DiesAfterTheNudge())

    result = app.agent.answer("How much protein should I eat?", THREAD)

    assert result.answer == OFF_THE_CUFF
    assert result.sources == ()


@pytest.mark.integration
def test_a_failure_after_the_second_look_worked_is_not_forgiven() -> None:
    """Once the gate's round has been and gone, the run is an ordinary run: an
    answer from before the search is not an answer to the search."""
    app = _app(_DiesAfterSearching())

    with pytest.raises(LlmError):
        app.agent.answer("How much protein should I eat?", THREAD)


@pytest.mark.integration
@pytest.mark.parametrize("budget", [3, 4, 5, 8])
def test_the_friendly_give_up_is_never_swallowed_by_the_gate(budget: int) -> None:
    """The apology is a verdict the router already reached; forgiving it would
    show work the run never did."""
    app = _app(_SearchesForever(), max_tool_rounds=budget)

    with pytest.raises(ToolLoopLimitError):
        app.agent.answer("How much protein should I eat?", THREAD)


@pytest.mark.integration
@pytest.mark.parametrize("budget", [1])
def test_a_budget_too_small_for_a_second_look_leaves_the_answer_alone(
    budget: int,
) -> None:
    """Sending an answer back with no room to read the evidence would spend the
    budget on a round that cannot finish, and end a good turn in an apology."""
    model = _SearchesForever()
    app = _app(model, max_tool_rounds=budget)

    result = app.agent.answer("How much protein should I eat?", THREAD)

    assert result.answer == OFF_THE_CUFF
    assert model.completions == 1


class _SearchesForever:
    def __init__(self) -> None:
        self.completions = 0

    def complete(
        self, messages: tuple[Message, ...], tools: tuple[Tool, ...]
    ) -> ModelReply:
        self.completions += 1
        if self.completions == 1:
            return ModelReply(text=OFF_THE_CUFF)
        return _searching()


@pytest.mark.integration
def test_a_plugin_that_declares_no_scope_answers_in_one_round() -> None:
    retriever = CountingRetriever()
    app = _app(ScriptedChatModel([ModelReply(text=OFF_THE_CUFF)]), retriever, scope="")

    result = app.agent.answer("How much protein should I eat?", THREAD)

    assert result.answer == OFF_THE_CUFF
    assert retriever.queries == 0


class _FailingRetrieverOnSearch(CountingRetriever):
    def query(self, query_vector, k):
        raise RetrievalError


@pytest.mark.integration
def test_a_second_look_whose_search_breaks_gives_back_the_answer_in_hand() -> None:
    """The search is the gate's own, and it is often the process's first, so an
    adapter failure there is likelier than anywhere. Losing a good answer to a
    round nothing asked for is the one thing the gate must never do."""
    model = ScriptedChatModel(
        [ModelReply(text=OFF_THE_CUFF), ModelReply(text=OFF_THE_CUFF)]
    )
    app = _app(model, _FailingRetrieverOnSearch())

    result = app.agent.answer("How much protein should I eat?", THREAD)

    assert result.answer == OFF_THE_CUFF
    assert result.sources == ()
    [looked] = [s for s in result.trace if isinstance(s, Reconsidered)]
    assert looked.failed


@pytest.mark.integration
def test_a_rescued_turn_says_the_second_look_never_came_back() -> None:
    seen: list[str] = []
    app = _app(_DiesAfterTheNudge())

    result = app.agent.answer(
        "How much protein should I eat?",
        THREAD,
        on_step=lambda s: seen.append(s.summary),
    )

    assert isinstance(result.trace[-1], SecondLookLost)
    assert result.trace[-1].failed
    assert seen[-1] == result.trace[-1].summary


@pytest.mark.integration
def test_the_shipped_scope_is_what_the_reminder_names() -> None:
    """Cora words the send-back; what the shipped plugin contributes is the phrase
    naming its documents, and that is what has to reach the model."""
    from cora.plugins.fitness import PLUGIN, SCOPE

    model = ScriptedChatModel([ModelReply(text=OFF_THE_CUFF), ModelReply(text="ok")])
    app = assembled(chat_model=model, retriever=CountingRetriever(), plugin=PLUGIN)

    app.agent.answer("How much protein should I eat?", THREAD)

    assert model.last_messages is not None
    sent_back = [m for m in model.last_messages if f"outside {SCOPE}" in m.content]
    assert len(sent_back) == 1


@pytest.mark.integration
def test_the_shipped_plugin_sends_an_ungrounded_answer_back() -> None:
    """Every other test here builds its own plugin, so the one cora actually
    ships could lose its scope and no test would notice."""
    from cora.plugins.fitness import PLUGIN

    model = ScriptedChatModel(
        [ModelReply(text=OFF_THE_CUFF), _searching(), ModelReply(text=GROUNDED)]
    )
    app = assembled(chat_model=model, retriever=CountingRetriever(), plugin=PLUGIN)

    result = app.agent.answer("How much protein should I eat?", THREAD)

    assert result.answer == GROUNDED
    assert any(isinstance(step, Reconsidered) for step in result.trace)


@pytest.mark.integration
def test_the_shipped_prompt_asks_for_the_users_own_documents() -> None:
    """The sprint-3 wording assumed the passages were already in the prompt; a
    plugin that still said it would be asking for something that never arrives."""
    from cora.plugins.fitness import PLUGIN

    model = ScriptedChatModel([ModelReply(text=OFF_THE_CUFF), ModelReply(text="ok")])
    app = assembled(chat_model=model, retriever=CountingRetriever(), plugin=PLUGIN)

    app.agent.answer("How much protein should I eat?", THREAD)

    assert model.last_messages is not None
    system = model.last_messages[0].content
    assert "retrieved context" not in system
    assert SEARCH_TOOL_NAME in system
