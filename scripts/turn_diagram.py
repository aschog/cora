"""One turn as it really runs: the ports are wrapped in a recorder, a scripted question
is asked, and the calls that happen are the messages. Who sends one is read off the
stack — the nearest frame belonging to a cora object is the sender — so the picture is
the engine's own call order rather than a drawing of what it ought to be."""

import inspect
from dataclasses import dataclass
from typing import Any

from cora.domain.prose import counted

QUESTION = "How does BM25 handle term saturation?"
DOCUMENT = ("bm25.txt", b"BM25 saturates term frequency so repeats stop helping.")
REMEMBERED = "trains on Tuesdays"
OUTSIDE = "User"
NAMES: dict[int, str] = {}


@dataclass
class Call:
    """Written down as the call is made, so a call the receiver makes in the middle of
    it lands after it rather than before; what came back is filled in on the way out."""

    sender: str
    receiver: str
    method: str
    arguments: str
    answer: str = ""


def _summary(value: Any) -> str:
    if isinstance(value, str):
        return f'"{value}"' if len(value) < 40 else f'"{value[:37]}..."'
    if isinstance(value, list | tuple):
        kinds = {type(item).__name__ for item in value}
        return counted(len(value), kinds.pop() if len(kinds) == 1 else "item")
    if isinstance(value, int | float | bool) or value is None:
        return str(value)
    return type(value).__name__


class Spy:
    """Every call through it is written down, then passed on untouched."""

    def __init__(self, name: str, inner: Any, log: list[Call]) -> None:
        self.name, self.inner, self.log = name, inner, log

    def __getattr__(self, attribute: str) -> Any:
        member = getattr(self.inner, attribute)
        if not callable(member):
            return member

        def recorded(*args: Any, **kwargs: Any) -> Any:
            shown = [*(_summary(a) for a in args), *(f"{k}=…" for k in kwargs)]
            call = Call(_sender(self), self.name, attribute, ", ".join(shown))
            self.log.append(call)
            answer = member(*args, **kwargs)
            call.answer = _summary(answer)
            return answer

        return recorded

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """A step is called, not asked — and `__call__` is looked up on the class, so
        it cannot be answered by `__getattr__` like every other member."""
        return self.__getattr__("__call__")(*args, **kwargs)


def spied(name: str, inner: Any, log: list[Call]) -> Any:
    """A recorder answers whatever it is asked for, so no port's Protocol describes it:
    it is handed over as `Any`, which is what a stand-in for anything is. The name it
    is given is the name its own code answers to as well: `LangGraphRunner` calling a
    step is `GraphRunner`, the slot it fills, on every line of the picture."""
    NAMES[id(inner)] = name
    return Spy(name, inner, log)


def _sender(receiver: Spy) -> str:
    """Whoever is making this call, found by walking out of the recorder answering it:
    the nearest frame belonging to a cora object, or to another recorder — a step is
    called by the graph engine, whose own frames belong to neither."""
    frame = inspect.currentframe()
    while frame is not None:
        caller = frame.f_locals.get("self")
        if isinstance(caller, Spy) and caller is not receiver:
            return caller.name
        if not isinstance(caller, Spy) and type(caller).__module__.startswith("cora."):
            return NAMES.get(id(caller), type(caller).__name__)
        frame = frame.f_back
    return OUTSIDE


def _named(call: Call) -> str:
    """A step is called rather than asked something, so `__call__` is no name to show.
    A reply that says no more than the call did is left out for the same reason: a step
    is handed the state and hands it back."""
    return "" if call.method == "__call__" else call.method


def sequence(question: str, answer: str, log: list[Call]) -> str:
    lines = [
        "sequenceDiagram",
        f'  {OUTSIDE}->>Agent: answer("{question}")',
        *(
            line
            for call in log
            for line in [
                f"  {call.sender}->>{call.receiver}: {_named(call)}({call.arguments})",
                *(
                    []
                    if call.answer == call.arguments
                    else [f"  {call.receiver}-->>{call.sender}: {call.answer}"]
                ),
            ]
        ),
        f"  Agent-->>{OUTSIDE}: {answer}",
    ]
    return "\n".join(lines)


def render() -> str:
    from app_builder import assembled, indexed
    from cora.adapters.langgraph_runner import langgraph_for
    from cora.ports.chat_model import ModelReply
    from cora.ports.plugin import ToolCall
    from fakes import FakeEmbedder, FakeMemory, FakeRetriever, ScriptedChatModel
    from fixture_plugins import make_plugin

    log: list[Call] = []
    model = ScriptedChatModel(
        [
            ModelReply(
                tool_calls=(
                    ToolCall(
                        name="search_documents",
                        arguments={"query": "term saturation"},
                        call_id="1",
                    ),
                )
            ),
            ModelReply(text="BM25 damps repeated terms [1]."),
        ]
    )
    memory = FakeMemory()
    memory.remember(REMEMBERED)
    app = indexed(
        assembled(
            chat_model=spied("ChatModel", model, log),
            embedder=spied("Embedder", FakeEmbedder(), log),
            retriever=spied("Retriever", FakeRetriever(), log),
            memory=spied("Memory", memory, log),
            plugin=make_plugin(),
            graph=lambda **steps: spied(
                "GraphRunner",
                langgraph_for(
                    **{
                        name: spied(type(step).__name__, step, log)
                        for name, step in steps.items()
                        if name != "max_tool_rounds"
                    },
                    max_tool_rounds=steps["max_tool_rounds"],
                ),
                log,
            ),
        ),
        DOCUMENT,
    )
    log.clear()
    result = app.agent.answer(QUESTION, thread_id="turn-diagram")
    return sequence(QUESTION, result.answer, log)


SECTIONS = (("turn", "One turn", "mermaid", render),)
