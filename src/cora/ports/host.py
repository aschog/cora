"""Cora as a plugin is handed it: what it may register, and what it may use."""

import logging
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol, overload

from cora.domain.card import Card
from cora.ports.chat_model import ChatModel
from cora.ports.context_source import ContextSource
from cora.ports.memory import Memory
from cora.ports.output import Output
from cora.ports.plugin import Tool
from cora.ports.store import Kept

CONTRACT = 1

TOOL = "tool"
HANDLER = "handler"
INSTRUCTIONS = "instructions"
PAGE = "page"

DEFAULT_SCOPE = "cora"

SCREENING = "screen"
BRIEFING = "brief"
CALLING = "tool_call"
RETURNING = "tool_result"
ANSWERING = "answer"

Handler = Callable[[Any], Any]


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
    `Memory`.

    Text, because what a plugin keeps is the plugin's own to read back. Reachable while
    a tool call of this plugin's is running, and outside one there is no conversation to
    keep anything for, so a read comes back with nothing and a write is dropped.
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


class FieldFiles(Protocol):
    """The files the field this turn runs in keeps, as the plugin that owns it reads.

    Text under a plain name, kept on disk where a person can open and edit it. Not the
    field's documents, which are chunked, embedded and cited — nothing indexes these,
    and what the text means is the plugin's own business.

    The field is the turn's rather than the plugin's to name, the way `documents` is:
    a plugin that could name a field could name somebody else's.
    """

    def names(self) -> tuple[str, ...]:
        """The names this field holds, sorted, or nothing where it holds none."""
        ...

    def read(self, name: str) -> str | None:
        """The text kept under this name, or nothing where nothing was."""
        ...

    def write(self, name: str, text: str | None) -> None:
        """Keep `text` under this name, replacing what was there.

        Args:
            text: The text to keep. `None` drops the name, and dropping a name nothing
                was kept under is not an error.
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


@dataclass(frozen=True)
class Contributed:
    """One registration as the listing shows it: what kind, what name, and where.

    `name` is the tool's name or the event a handler subscribed to, and blank where the
    kind has no name of its own, as a section of the brief has not. One field over every
    kind, so a fourth kind is listed without this shape widening.

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

        One reader over the kinds rather than a property per kind: a fourth kind is
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

    def register_page(self, directory: str | os.PathLike[str], *, scope: str) -> None:
        """Bring one field its own page: a directory served whole, entry page first.

        Where a shell draws it is the shell's rule and nothing here says. Everything
        under the directory is served to whoever reaches cora, so put nothing there
        that should not be published, and know that a symlink out of it is not followed.

        Args:
            directory: What to serve, as this plugin holds it. It is read at the
                request rather than here, the disk being free to change after any
                check, so one that is not there costs its own path a refusal and
                nothing else.
            scope: The field whose page this is. Required, where every other
                registration may be system-wide: a page belongs to a subject.

        Raises:
            PluginLoadError: No field was named, or this plugin already brought that
                field a page.
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
    def store(self) -> Kept | None:
        """This plugin's own store, or nothing where the deployment keeps none.

        What is kept there outlives the conversation and the process, which `state`
        does not — and it is the plugin's own, which `memory` is not. Absent rather
        than empty where there is nowhere to keep anything, so a plugin that needs one
        can say so instead of losing every write.
        """
        ...

    @property
    def state(self) -> State:
        """What this plugin kept for the conversation this turn is answering on."""
        ...

    @property
    def files(self) -> FieldFiles:
        """The files the field this turn runs in keeps, which are not its documents.

        Where `store` is this plugin's own text by name and `documents` is what the
        user uploaded, these are the field's own data on disk: nothing indexes them,
        and a person can open them in an editor.
        """
        ...

    @overload
    def delegate(
        self, task: str, tools: tuple[Tool, ...] = (), rounds: int = 3
    ) -> str: ...

    @overload
    def delegate(
        self,
        task: str,
        tools: tuple[Tool, ...] = (),
        rounds: int = 3,
        *,
        shape: Mapping[str, Any],
    ) -> dict[str, Any]: ...

    def delegate(
        self,
        task: str,
        tools: tuple[Tool, ...] = (),
        rounds: int = 3,
        *,
        shape: Mapping[str, Any] | None = None,
    ) -> str | dict[str, Any]:
        """Run a bounded loop of the model's own, and answer with what it wrote.

        The loop is offered the tools given plus cora's document search, and never a
        tool that writes, stops the turn, or declares an effect — one passed in that
        declares one is withheld, and the plugin's logger says which. Its steps are
        reported under the call that ran it, and what it answers reaches the turn
        labelled untrusted and citing nothing of its own. One that spends its rounds
        without an answer is asked once more, with no tools, to write up what it found.

        Given a shape, the loop answers by calling a tool that takes it: the value
        comes back checked, and a failed check is told to the loop to correct.

        Args:
            task: What the loop is being asked to do, as its first message.
            tools: What it may call, on top of searching the documents.
            rounds: How many rounds it may spend, capped by the host and ignored in a
                loop delegated from another. One more than this reaches the model, the
                last with the tools still on the table so a loop can answer in it.
            shape: JSON Schema the answer must satisfy, and what the loop is offered as
                the parameters of its answer. It must require something, an answer
                satisfying a shape that requires nothing being an empty one. A `format`
                in it is not checked, so a caller wanting dates read still reads them.

        Raises:
            ToolRefusal: The loop gathered nothing before its rounds ran out, or the
                write-up came back empty, or a tool passed in takes a name of cora's
                own. With a shape: the shape is not one anything could be held to, the
                loop wrote prose instead of answering in it, or its rounds ran out.
                Either way the call fails and the turn answers anyway.
            LlmError: The model gave back nothing usable.
        """
        ...


Extend = Callable[[Host], None]


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
