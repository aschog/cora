from collections.abc import Callable

from cora.domain.decision import Decision

Pause = Callable[[Decision], str | None]
"""How a step stops the run and waits. It travels *in*, like `TextSink`, because only
whatever is driving the graph can park a run and pick it up again — the engine states
the decision and is handed back the label chosen, or nothing at all if the user
declined."""


def declined(_: Decision) -> None:
    """The pause of a caller that cannot stop and ask: the decision is declined the
    moment it is raised, so a shell with no card to draw still gets its answer. Every
    slot that takes a `Pause` defaults to this, which is what keeps a run that cannot
    be interrupted from hanging on one."""
