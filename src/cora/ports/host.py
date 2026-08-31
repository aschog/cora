"""Cora as a plugin is handed it: what it may register, and what it may use."""

import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from cora.ports.chat_model import ChatModel
from cora.ports.context_source import ContextSource
from cora.ports.memory import Memory
from cora.ports.plugin import Tool

TOOL = "tool"
HANDLER = "handler"
INSTRUCTIONS = "instructions"
"""What a plugin can register. A kind is a field rather than a class, so the listing,
the collision check and the log line are each written once over one list — and a fifth
kind is a method on `Host` and an entry here, not a shape anyone has to widen."""

DEFAULT_SCOPE = "cora"
"""The field a turn belonging to none of the loaded ones runs in.

A name rather than an empty set, so a turn can always say which scope it ran under and
a scope always has somewhere to keep its documents. Nothing cora ships registers under
it: it is what a bare cora is, and a plugin that registers here says "in every field,
and in none".
"""

SCREENING = "screen"
BRIEFING = "brief"
CALLING = "tool_call"
RETURNING = "tool_result"
"""The points in a turn a handler can be subscribed to, under the names a plugin writes:
the question being screened, the brief being settled, a tool call about to run, and a
tool result coming back. A name is contract, which is why it is here; what a handler's
return *means* at each is `cora.engine.events`, which is not."""

Handler = Callable[[Any], Any]
"""What a handler is: one frozen value in, and one decision out.

Answering with `None` is answering with nothing, and changes nothing. What else may be
answered depends on the event — a refusal where an event refuses, an amendment where it
amends — and what is handed in is that event's value: the question, the brief, a
`ToolCall`, a `ToolResult`. A handler is never handed the turn's state, and nothing it
returns reaches the state except through the event it answered.
"""


@dataclass(frozen=True)
class Subscription:
    """One handler, and the point in the turn it was subscribed to."""

    event: str
    handle: Handler


@dataclass(frozen=True)
class Registration:
    """One thing a plugin registered, and the module that registered it.

    The module is what a refusal quotes back, because it is what the deployment typed.
    `value` is read according to `kind`, in the one place that turns registrations into
    what a turn takes. `scope` is where it applies: a name the turn has to be running
    under, or `None` for everywhere — and nothing a scope can switch off.
    """

    module: str
    kind: str
    value: Any
    scope: str | None = None


class Host(Protocol):
    """Cora, as a plugin is handed it: what cora has, and where to register its own.

    A plugin is limited by what this offers rather than by fields it fills in, so a new
    kind of contribution is a method here. Everything handed over is the port cora
    itself holds, not a copy — a plugin searching the documents searches the index the
    uploads went into.
    """

    def register_tool(
        self,
        *,
        name: str,
        description: str,
        parameter_schema: dict[str, Any],
        run: Callable[..., Any],
        scope: str | None = None,
    ) -> None:
        """Offer the model one more thing it can do, as `Tool` describes one.

        Args:
            scope: Where it is offered. `None` offers it in every turn.
        """
        ...

    def register_handler(
        self, *, event: str, handle: Handler, scope: str | None = None
    ) -> None:
        """Take part in the turn at one of the points this module names.

        Args:
            event: One of `SCREENING`, `BRIEFING`, `CALLING`, `RETURNING`.
            handle: What runs there, as `Handler` describes one.
            scope: Where it runs. `None` runs it in every turn, and no scope can
                switch that off — which is what screening for injection needs.
        """
        ...

    def register_instructions(
        self, instructions: str, scope: str | None = None
    ) -> None:
        """Say what this plugin is for, as a section of the model's brief.

        Args:
            scope: Where the section appears. `None` puts it in every brief.
        """
        ...

    @property
    def documents(self) -> ContextSource:
        """What the user uploaded, searchable as cora's own tool searches it.

        The index the uploads went into, not a copy of it. Searching it says so: what a
        plugin answers a call with after reading a passage reaches the model behind the
        same untrusted label the passage itself would have.
        """
        ...

    @property
    def memory(self) -> Memory | None:
        """What cora keeps about the user, or nothing where a deployment kept none."""
        ...

    @property
    def model(self) -> ChatModel:
        """The model behind every turn, for a plugin that wants to ask it something."""
        ...

    @property
    def log(self) -> logging.Logger:
        """A logger named for this plugin, so its lines say which plugin wrote them."""
        ...

    @property
    def settings(self) -> Mapping[str, str]:
        """This plugin's own settings, read from the environment under its own name."""
        ...

    def delegate(self, task: str, tools: tuple[Tool, ...] = (), rounds: int = 3) -> str:
        """Run a bounded loop of the model's own, and answer with what it wrote.

        The loop is offered the tools given plus cora's document search, and none of
        cora's own tools that write or stop the turn: an effect and a stop-to-ask
        belong in the turn around it, where the gate is. Its steps are reported under
        the call that ran it, and what it answers carries no citation of its own — and
        reaches the turn labelled untrusted, because the documents went into it.

        Args:
            task: What the loop is being asked to do, as its first message.
            tools: What it may call, on top of searching the documents.
            rounds: How many rounds of tools it may spend, capped by the host and
                ignored in a loop delegated from another.

        Raises:
            ToolRefusal: The loop spent its rounds without reaching an answer, or a
                tool passed in takes the name cora's own search has. Either way the
                call fails and the turn around it answers anyway.
            LlmError: The model gave back nothing usable.
        """
        ...


Extend = Callable[[Host], None]
"""What a plugin module defines: `extend(cora)`, called once with a host of its own."""


@dataclass(frozen=True)
class Extension:
    """A plugin module that imported, and the call that registers what it has.

    Loading proves the module is there and defines `extend`; registering happens later,
    against a host, because a host needs the parts an assembled app holds.
    """

    module: str
    extend: Extend
