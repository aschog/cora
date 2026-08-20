"""How a turn is walked: the steps, the routing between them, and who drives it."""

from collections.abc import Callable, Iterator
from typing import Protocol

from cora.domain.agent_state import AgentState
from cora.domain.decision import Pending
from cora.ports.chat_model import TextSink, unheard

DONE = "done"
TOOLS = "tools"
ASK = "ask"
"""What the router can decide, and therefore what a `GraphRunner` has to understand. It
belongs beside the port for the same reason `AgentState` marks its accumulating keys: a
graph engine is told the shape and the vocabulary, and imports nothing of the engine to
learn them."""


class Step(Protocol):
    """One move of a turn: state in, the keys it contributed out."""

    def __call__(self, state: AgentState) -> AgentState:
        """Take the step and return *only* what it added.

        Never the whole state: the accumulating keys are appended to by whatever drives
        the graph, so a step that handed its inputs back would double them.
        """
        ...


Route = Callable[[AgentState], str]
ModelFor = Callable[[TextSink], Step]
"""How a graph asks for the step that talks to the model: one per turn, bound to that
turn's reader. The other two steps are the same for every turn and are handed over as
themselves; this one is not, because an app assembled once answers two readers at once
and neither may be sent the other's text."""


class GraphRunner(Protocol):
    """Drives one turn of the agent's steps on a named thread.

    Yields the state as it accumulates: the thread as the turn found it, then one state
    per step taken, the last of them the finished turn. A thread remembers its own
    conversation, so a second turn is seeded with the question alone. Core errors raised
    inside a step travel out of the iteration unwrapped — and the state yielded last may
    predate such a failure, so it is no evidence about what the run had reached when it
    failed.
    """

    def run(
        self, state: AgentState, thread_id: str, on_text: TextSink = unheard
    ) -> Iterator[AgentState]:
        """Walk a turn on a thread, yielding the state after each step.

        Args:
            state: What this turn adds to the thread — the question and the brief, not
                the conversation, which the thread already holds.
            thread_id: The conversation to continue. One it has never seen starts one.
            on_text: Handed to the step that talks to the model, so this turn's prose
                reaches this caller and no other.

        Raises:
            ToolLoopLimitError: The turn asked for more rounds than it was allowed.
        """
        ...

    def resume(
        self, answer: str | None, thread_id: str, on_text: TextSink = unheard
    ) -> Iterator[AgentState]:
        """The same turn, picked up from where it stopped to ask.

        Args:
            answer: The label the user chose, or nothing if they declined.
            thread_id: The thread whose turn is parked.
            on_text: As in `run` — the rest of the turn is written to this caller.

        Yields:
            As `run` does, continuing the parked turn rather than starting one.

        Raises:
            NothingToResumeError: That thread is not waiting on a decision.
        """
        ...

    def pending(self, thread_id: str) -> Pending | None:
        """What the thread is waiting on, or nothing.

        A parked run stops yielding rather than saying so, so this is the only way to
        tell a turn that stopped to ask from one that finished.
        """
        ...


class GraphFor(Protocol):
    """How a composition root asks for a runner.

    It has the steps and the router already; the round budget is passed because a graph
    engine may need to size a limit of its own from it. Which engine walks them is the
    slot's to decide, like every other port — without this the graph was the one slot
    the wiring hard-coded.
    """

    def __call__(
        self,
        *,
        prepare: Step,
        model: ModelFor,
        tools: Step,
        ask: Step,
        router: Route,
        max_tool_rounds: int,
    ) -> GraphRunner:
        """Build a runner over these steps.

        Args:
            prepare: Opens a turn — the brief, the rules, the question.
            model: Asked once per turn for the step bound to that turn's reader.
            tools: Runs the calls a round asked for.
            ask: Stops the turn to put a decision to the user.
            router: Reads a state and names what comes next: `DONE`, `TOOLS` or `ASK`.
            max_tool_rounds: How many rounds of tools a turn may spend.
        """
        ...
