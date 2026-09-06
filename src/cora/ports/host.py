"""Cora as a plugin is handed it: what it may register, and what it may use."""

import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from cora.domain.card import Card
from cora.ports.chat_model import ChatModel
from cora.ports.context_source import ContextSource
from cora.ports.memory import Memory
from cora.ports.output import Output
from cora.ports.plugin import Tool

CONTRACT = 1
"""The version of this contract cora offers, and what a plugin declares to ask for.

A number rather than a range: cora offers one version, a plugin declaring another is
refused by name, and a plugin declaring none is taken as asking for this one. What is
public is everything this module names; what may move is said on the page that teaches
a plugin to be written.

It moves when the contract *changes*, not when it grows. Surface added to `Host` — a
register keyword, a property like `output` — leaves it where it is, because a plugin
asking for this version still gets everything this version promised. The cost is that a
plugin needing something newly added cannot say so, and finds out by the call failing
rather than at the version check.
"""

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
ANSWERING = "answer"
"""The points in a turn a handler can be subscribed to, under the names a plugin writes:
the question being screened, the brief being settled, a tool call about to run, a tool
result coming back, and the answer settled and not yet handed over. A name is contract,
which is why it is here; what a handler's return *means* at each is
`cora.engine.events`, which is not."""

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


class State(Protocol):
    """What one plugin kept for the conversation a turn is answering on.

    Names are the plugin's own: two plugins choosing one name keep two values, and
    neither can read the other's. What is kept lasts as long as the conversation does
    and goes when it is deleted — it is not what cora knows about the user, which is
    `Memory` and outlives every conversation.

    Text, because what a plugin keeps is the plugin's own to read back. A shape richer
    than that would make cora the reader of it.

    Reachable while a tool call of this plugin's is running, which is where a plugin's
    own code runs inside a turn. Outside one there is no conversation to keep anything
    for, so a read comes back with nothing and a write is dropped.
    """

    def read(self, name: str) -> str | None:
        """What was kept under this name, or nothing where nothing was."""
        ...

    def keep(self, name: str, value: str | None) -> None:
        """Keep `value` under this name for the rest of this conversation.

        Args:
            value: The text to keep. `None` drops the name.
        """
        ...


@dataclass(frozen=True)
class Registration:
    """One thing a plugin registered, and the module that registered it.

    The module is what a plugin is known by — what the deployment typed, or the stem
    of a file dropped in the plugins folder. `value` is read according to `kind`, in
    the one place that turns registrations into what a turn takes. `scope` is where it
    applies: a name the turn has to be running under, or `None` for everywhere — and
    nothing a scope can switch off.
    """

    module: str
    kind: str
    value: Any
    scope: str | None = None


def name_of(module: str) -> str:
    """What a plugin is called: the last segment of what it was loaded under.

    One rule in one place, because four things are named by it — the heading of its
    section in the brief, the settings it may read, the logger its lines carry, and the
    name two plugins may not share. A file dropped in the plugins folder is loaded under
    its own stem, so this is that stem.
    """
    return module.rsplit(".", 1)[-1]


HAS_AN_EFFECT = "has an effect"
"""What a tool that changes something outside cora is listed as. One wording for both
renderings — the terminal's and the page's — because it is the same claim, and the
reader deciding whether to load a plugin is asking it of both."""


@dataclass(frozen=True)
class Contributed:
    """One registration as the listing shows it: what kind, what name, and where.

    `name` is the tool's name or the event a handler subscribed to, and blank where the
    kind has no name of its own, as a section of the brief has not. One field over every
    kind, so a fifth kind is listed without this shape widening.

    `note` is whatever else this registration says about itself, in words a reader can
    take at face value — a tool that has an effect says so here. A note rather than a
    field per property, for the same reason `name` is one field: a rendering shows it
    without having heard of what it means.
    """

    kind: str
    name: str
    scope: str | None = None
    note: str = ""

    @property
    def system_wide(self) -> bool:
        """Whether this applies to every turn, no scope being able to switch it off."""
        return self.scope is None


@dataclass(frozen=True)
class Listed:
    """One loaded plugin, and everything it registered.

    `name` is its last segment — what heads its section of the brief and names its
    settings — and `source` is where it was found: a module path, or a file.
    """

    name: str
    source: str
    contributions: tuple[Contributed, ...] = ()

    @property
    def scopes(self) -> tuple[str, ...]:
        """Every field it registered under, once each, in registration order."""
        named = [each.scope for each in self.contributions if each.scope is not None]
        return tuple(dict.fromkeys(named))

    def of(self, kind: str) -> tuple[Contributed, ...]:
        """Everything it registered of one kind, in the order it registered them.

        One reader over the kinds rather than a property per kind: a fifth kind is
        already listed, and would otherwise want a fourth accessor to be read by.
        """
        return tuple(each for each in self.contributions if each.kind == kind)


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
        untrusted: bool = False,
        effect: bool = False,
        asks: Callable[[dict[str, Any]], Card | None] | None = None,
    ) -> None:
        """Offer the model one more thing it can do, as `Tool` describes one.

        Args:
            scope: Where it is offered. `None` offers it in every turn.
            untrusted: Whether what it returns is material cora did not write — a
                service it called, a page it read. What such a tool returns reaches
                the model behind the label a passage of the user's own documents has,
                and no handler can take it off.
            effect: Whether calling it changes something outside cora. Such a tool is
                never offered to a delegated loop, so an effect stays in the turn the
                user is watching, and the listing says the plugin has one.
            asks: What to put to the user before this call is made, given the arguments
                the model wrote — or nothing, to run as called. What they fill in is
                written over those arguments, so the tool is called once and with values
                a person stated. It must be pure: the step that puts the card is
                replayed on every pick-up, so it is called again each time, and one
                whose answer varies moves the pause the reader already settled.
        """
        ...

    def register_handler(
        self, *, event: str, handle: Handler, scope: str | None = None
    ) -> None:
        """Take part in the turn at one of the points this module names.

        Args:
            event: One of `SCREENING`, `BRIEFING`, `CALLING`, `RETURNING`, `ANSWERING`.
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

    def show(self, did: str, detail: str = "", failed: bool = False) -> None:
        """Say what this plugin's own code just did, as one line on the trace.

        Cora fills in which plugin said it, so a line can never be signed with another
        plugin's name. It lands among the steps of the tool call it was said inside,
        beside the rounds a delegated loop reports there. Said outside a call there is
        nothing to report to, and it is dropped.

        Args:
            did: The line the reader sees, in the plugin's own words.
            detail: What is behind the line, for a reader who opens it.
            failed: Whether what it describes went wrong. A failed line is still shown,
                and does not end the turn.
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
    def output(self) -> Output | None:
        """Where an effect may write what it produced, or nothing where none is set.

        The port and never a path: a plugin holds the ability to write in the one place
        the deployment allows, and the check that a name stays there is the adapter's.
        A plugin whose tool needs it registers that tool only when there is one, the way
        cora offers no `remember` without a memory.
        """
        ...

    @property
    def log(self) -> logging.Logger:
        """A logger named for this plugin, so its lines say which plugin wrote them."""
        ...

    @property
    def settings(self) -> Mapping[str, str]:
        """This plugin's own settings, read from the environment under its own name."""
        ...

    @property
    def state(self) -> State:
        """What this plugin kept for the conversation this turn is answering on."""
        ...

    def delegate(self, task: str, tools: tuple[Tool, ...] = (), rounds: int = 3) -> str:
        """Run a bounded loop of the model's own, and answer with what it wrote.

        The loop is offered the tools given plus cora's document search, and never a
        tool that writes, stops the turn, or declares an effect — one passed in that
        declares one is withheld, and the plugin's logger says which. An effect and a
        stop-to-ask belong in the turn around it, where the gate is. Its steps are
        reported under the call that ran it, and what it answers carries no citation of
        its own — and reaches the turn labelled untrusted, because the documents went
        into it.

        A loop that spends every round without reaching an answer is asked once more,
        with no tools, to write up what it found: the rounds it spent are not lost, and
        what comes back says it stopped early rather than reading as a whole answer.

        Args:
            task: What the loop is being asked to do, as its first message.
            tools: What it may call, on top of searching the documents.
            rounds: How many rounds it may spend, capped by the host and ignored in a
                loop delegated from another. One more than this reaches the model, the
                last with the tools still on the table so a loop can answer in it.

        Raises:
            ToolRefusal: The loop gathered nothing before its rounds ran out, or the
                write-up came back empty, or a tool passed in takes the name cora's own
                search has. Either way the call fails and the turn answers anyway.
            LlmError: The model gave back nothing usable.
        """
        ...


Extend = Callable[[Host], None]
"""What a plugin module defines: `extend(cora)`, called once with a host of its own."""


@dataclass(frozen=True)
class Extension:
    """A plugin module that imported, and the call that registers what it has.

    Loading proves the module is there and defines `extend`; registering happens later,
    against a host, because a host needs the parts an assembled app holds. `source` is
    where it was found and what every refusal quotes: the module path a deployment
    named, or the file it was read from. A named module is its own source, so leaving it
    out says "named rather than dropped".
    """

    module: str
    extend: Extend
    source: str = ""

    def __post_init__(self) -> None:
        """Take the module path as the source where none was given."""
        if not self.source:
            object.__setattr__(self, "source", self.module)
