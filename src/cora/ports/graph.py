"""How a turn is walked: the steps, the routing between them, and who drives it."""

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Protocol

from cora.domain.agent_state import AgentState
from cora.domain.approval import Approval
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


class NamedStep(Protocol):
    """A step under the name of the place a turn is in while it takes that step.

    The name is what a turn can be reported as being *in*: it heads that step's trace
    and it names the step a failure came out of. Which is why a graph is handed these
    rather than bare steps — a node has to be called something, and this is the name.
    """

    @property
    def step(self) -> str:
        """The step's name, and the name of the node that runs it."""
        ...

    def __call__(self, state: AgentState) -> AgentState:
        """As `Step`: the keys this step contributed, and no others."""
        ...


Settled = str | Approval | None
"""What travels back into a parked turn: a label off a card, an approval bound to one
call, or nothing at all. One type because one thread stops one way at a time and the
caller picking it up hands over whichever it was asked for."""

Route = Callable[[AgentState], str]
ModelFor = Callable[[TextSink], Step]
"""How a graph asks for the step that talks to the model: one per turn, bound to that
turn's reader. The other steps are the same for every turn and are handed over as
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
        self, answer: Settled, thread_id: str, on_text: TextSink = unheard
    ) -> Iterator[AgentState]:
        """The same turn, picked up from where it stopped.

        Args:
            answer: The label the user chose, the approval they gave, or nothing if they
                declined. Each step that can stop checks what came back to it, so an
                answer of the other kind settles nothing it was not asked.
            thread_id: The thread whose turn is parked.
            on_text: As in `run` — the rest of the turn is written to this caller.

        Yields:
            As `run` does, continuing the parked turn rather than starting one.

        Raises:
            NothingToResumeError: That thread is not waiting on anything.
        """
        ...

    def pending(self, thread_id: str) -> Pending | None:
        """What the thread is waiting on, or nothing.

        A parked run stops yielding rather than saying so, so this is the only way to
        tell a turn that stopped from one that finished.
        """
        ...

    def forget(self, thread_id: str) -> None:
        """Drop everything a thread holds: its pin, its transcript, its parked turn.

        A thread nobody has asked anything on is not an error. A thread forgotten while
        a turn was parked in it is waiting on nothing, so resuming it is refused as any
        thread waiting on nothing is.
        """
        ...

    def pinned(self, thread_id: str) -> str | None:
        """The scope this thread was pinned to, or nothing.

        The pin is a key of the thread's own state, so the runner is what can read it —
        and it has to be readable outside a turn: a page reopening a conversation draws
        the pin before anyone asks anything, and a second, different pin is refused
        before a turn is started on it.
        """
        ...


@dataclass(frozen=True)
class Loop:
    """The rounds of a turn, and the parts that take one.

    Named apart from the steps around it because it alone has a router and it alone may
    stop. `marker` is the step the rounds fall inside: it runs once, contributes the
    name of the place the turn is in, and leaves the round to the model. `gate` stands
    between the model and the tools, on every round, so no call reaches a tool without
    passing it — a round proposing nothing that changes anything outside cora passes
    straight through. `ask` is handed over like the rest: an app that offers no decision
    says so with a step that puts none, rather than with a slot left empty.
    """

    marker: NamedStep
    model: ModelFor
    gate: Step
    tools: Step
    router: Route
    ask: Step


class GraphFor(Protocol):
    """How a composition root asks for a runner.

    The turn is handed over as a sequence — what runs before the rounds, the rounds,
    and what runs after them — so a step added to a turn is added there and not here.
    The round budget is passed because a graph engine may need to size a limit of its
    own from it. Which engine walks the sequence is the slot's to decide, like every
    other port.
    """

    def __call__(
        self,
        *,
        before: tuple[NamedStep, ...],
        loop: Loop,
        after: tuple[NamedStep, ...],
        max_tool_rounds: int,
    ) -> GraphRunner:
        """Build a runner over this walk.

        Args:
            before: The steps a turn takes before its first round, in order.
            loop: The rounds, and what takes one.
            after: The steps a turn takes once the rounds are done, in order. The last
                of them settles the answer; a walk that settles none walks and finishes
                but cannot answer a turn.
            max_tool_rounds: How many rounds of tools a turn may spend.
        """
        ...
