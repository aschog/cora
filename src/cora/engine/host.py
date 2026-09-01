"""Cora as one plugin is handed it, and where what that plugin registers is kept."""

import logging
import re
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any

from jsonschema import Draft202012Validator, SchemaError

from cora.domain.citations import Citable
from cora.domain.errors import PluginLoadError
from cora.engine.events import EVENTS
from cora.engine.nesting import collecting, read_untrusted, took
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME, search_tool
from cora.engine.rounds import Read, decided, told, used
from cora.engine.scoping import here
from cora.engine.tool_runtime import ToolRuntime
from cora.ports.chat_model import ChatModel, Message
from cora.ports.context_source import ContextSource
from cora.ports.host import (
    HANDLER,
    INSTRUCTIONS,
    TOOL,
    Handler,
    Registration,
    Subscription,
    name_of,
)
from cora.ports.memory import Memory
from cora.ports.plugin import Tool, ToolRefusal, ToolResult
from cora.ports.retrieval import RetrievedChunk

DELEGATE_BRIEF = (
    "You are answering one question on behalf of an assistant, using the tools you are "
    "offered. Be brief and concrete, and answer from what the tools return. Name the "
    "document a fact came from in your own words — never write a citation number, "
    "because the numbers belong to the assistant and not to you."
)
MAX_DELEGATED_ROUNDS = 5
"""The most rounds a delegated loop may spend, whatever it asks for. The budget is the
host's rather than the plugin's: one tool call that asked for ten thousand rounds would
spend a deployment's bill. It bounds a *call* — a round of the turn's own may make
several, and a turn several rounds, so what a turn can spend on delegation is this times
what `Router` allows it. Bounded, not small."""
OVERSPENT = (
    "the sub-agent ran out of rounds without reaching an answer; ask it something "
    "narrower, or answer without it"
)
"""What the model is told when a delegated loop gives up. A sentence rather than a
failure of the turn's: the turn has rounds left, and this is one call it cannot use."""
_allowance: ContextVar[list[int] | None] = ContextVar("_allowance", default=None)
"""What is left of the rounds this delegation may spend, shared by every loop under it.

A delegated loop may call a tool that delegates again, and a fresh budget per level
would make depth a way of asking for more — four levels of five rounds is a thousand
model calls from one tool call. The outermost loop opens the pot and everything inside
it spends the same one, so a tool call costs what the host allows however deep the
plugin goes."""
CITED = r"(?:\[\d+\])+"
"""A run of bracketed numbers, as `CITATION_RUN` counts one. What may precede it is the
question below, and it is a narrower question here than on the page."""
OPENS = r"=([{<>|&^~/\\+"
"""What a bracketed run is *not* a citation after: an assignment, an opener, an
operator. Written as what disqualifies rather than as what qualifies, because prose has
more shapes than code does — a claim is cited after bold, after a percent, after a
closing backtick, and a list of everything a sentence may end in is a list that keeps
being wrong."""
UNCITED = re.compile(rf"(?<=[^\s{OPENS}])[ \t]+{CITED}")
"""What a delegated loop's answer is stripped of, should it write a number anyway. A
citation follows what it cites and then a space: `weights = [1]` is a literal and
`arr[0]` an index, and neither is cora's business. Taking the space with the run leaves
the sentence closed up without touching the rest of the line."""
OPENED_WITH = re.compile(rf"^([ \t]*(?:[-*+][ \t]+)?){CITED}[ \t]*")
"""A number the line opened with, and the space it left behind. Whatever indentation and
list marker stood in front of it is the loop's own and is handed back untouched."""
FENCE = re.compile(r"^[ \t]*(```|~~~)")
"""What opens a fenced block, and the marker it was opened with — a block is closed by
its own marker, so a tilde line inside a backtick block is content. Nothing inside one
is prose, so nothing inside one is a citation: a loop explaining code writes numbers
that are the code's own."""


PLUGIN_LOGGER = "cora.plugin"
"""Where a plugin's own logger hangs. Under cora, so one switch configures every line
the app writes, and singular so it is a logger rather than the namespace a distribution
installs into."""


@dataclass
class PluginHost:
    """What one plugin's `extend` is called with, and what it registered afterwards.

    One host per plugin, so a log line and a setting are named for the plugin that read
    them, and so a registration knows which module made it. The ports are cora's own:
    a plugin searching the documents searches the index the uploads went into.
    """

    module: str
    index: ContextSource
    model: ChatModel
    memory: Memory | None = None
    settings: Mapping[str, str] = field(default_factory=dict)
    top_k: int = 5
    registered: list[Registration] = field(default_factory=list)

    @property
    def documents(self) -> ContextSource:
        """What the user uploaded, searched the way cora's own tool searches it.

        The index itself, not a copy — a plugin searching the documents searches what
        the uploads went into. What is added is the saying-so: a plugin reads passages
        for its own reasons, and whatever it does with them, the call it did it in
        answers for material cora does not vouch for.
        """
        return _Reading(self.index)

    @property
    def log(self) -> logging.Logger:
        """A logger named for this plugin, so its lines say which plugin wrote them.

        Under cora's own namespace rather than under the plugin's module path: the
        debug handlers are attached to cora's logger and nowhere else, and a plugin
        installed from anywhere — a file dropped in a folder most of all — would
        otherwise write into a logger nothing is listening to.
        """
        return logging.getLogger(f"{PLUGIN_LOGGER}.{name_of(self.module)}")

    def register_tool(
        self,
        *,
        name: str,
        description: str,
        parameter_schema: dict[str, Any],
        run: Callable[..., Any],
        scope: str | None = None,
    ) -> None:
        """Offer the model one more thing it can do.

        Raises:
            PluginLoadError: The tool cannot be offered — a blank name, a name this
                plugin already registered, something that cannot be called, or a
                parameter schema that is not valid JSON Schema.
        """
        if not name.strip():
            raise PluginLoadError(self.module, "a tool was registered with no name")
        if not callable(run):
            raise PluginLoadError(self.module, f"tool '{name}' has no callable run")
        if any(tool.name == name for tool in self._registered_tools()):
            raise PluginLoadError(self.module, f"tool '{name}' was registered twice")
        try:
            Draft202012Validator.check_schema(parameter_schema)
        except SchemaError as invalid:
            raise PluginLoadError(
                self.module, f"tool '{name}' has an invalid parameter schema"
            ) from invalid
        self._record(
            TOOL,
            Tool(
                name=name,
                description=description,
                parameter_schema=parameter_schema,
                run=run,
            ),
            scope,
        )

    def register_handler(
        self, *, event: str, handle: Handler, scope: str | None = None
    ) -> None:
        """Take part in the turn at one of the points `cora.ports.host` names.

        Raises:
            PluginLoadError: Cora has no such event, the handler cannot be called, or a
                class was registered where a function belongs — a class is callable, so
                a check that only asked whether it could be called would subscribe a
                constructor and refuse every question with whatever it built. All three
                are refused at startup: a handler runs once a turn is under way, and one
                left to be found there is a question dying halfway through.
        """
        if event not in EVENTS:
            raise PluginLoadError(
                self.module, f"there is no '{event}' point in a turn to subscribe to"
            )
        if not callable(handle) or isinstance(handle, type):
            raise PluginLoadError(
                self.module, f"the handler for '{event}' is not a function to call"
            )
        self._record(HANDLER, Subscription(event=event, handle=handle), scope)

    def register_instructions(
        self, instructions: str, scope: str | None = None
    ) -> None:
        """Say what this plugin is for, as a section of the model's brief.

        Raises:
            PluginLoadError: The instructions are not text. What heads a section of the
                brief has to be readable by the model that reads the brief.
        """
        if not isinstance(instructions, str):
            raise PluginLoadError(self.module, "instructions must be a string")
        self._record(INSTRUCTIONS, instructions, scope)

    def delegate(self, task: str, tools: tuple[Tool, ...] = (), rounds: int = 3) -> str:
        """Run a bounded loop of the model's own, and answer with what it wrote.

        Offered the tools given plus cora's document search, and none of cora's own
        tools that write or stop the turn. Every round is reported to the call this ran
        inside, so a reader sees the loop's work under the tool that ran it. What comes
        back cites nothing: the numbers a reader can click belong to the turn.

        Args:
            task: What the loop is being asked to do, as its first message.
            tools: What it may call, on top of searching the documents.
            rounds: How many rounds of tools it may spend, up to
                `MAX_DELEGATED_ROUNDS`. Ignored in a loop delegated from another,
                which spends what the outermost one opened.

        Raises:
            ToolRefusal: The loop spent its rounds without reaching an answer, or a
                tool passed in takes the name cora's search already has. The call fails
                and the model is told why; the turn around it answers anyway.
            LlmError: The model gave back nothing usable.
        """
        offered = self._offered(tools)
        runtime = ToolRuntime(tools=offered)
        said: list[Message] = [
            Message(role="system", content=DELEGATE_BRIEF),
            Message(role="user", content=task),
        ]
        with _spending(rounds) as left:
            return self._rounds(said, offered, runtime, left)

    def _rounds(
        self,
        said: list[Message],
        offered: tuple[Tool, ...],
        runtime: ToolRuntime,
        left: list[int],
    ) -> str:
        """One delegated loop, spending the allowance the outermost one opened.

        Raises:
            ToolRefusal: The allowance ran out before the loop answered. A refusal
                rather than a loop limit of the turn's own: the turn did not overspend,
                one of its calls did, and the model is owed a sentence saying so.
        """
        while left[0] > 0:
            left[0] -= 1
            reply = self.model.complete(tuple(said), offered)
            took(decided(reply))
            if reply.is_final:
                return _uncited(reply.text)
            said.append(
                Message(
                    role="assistant", content=reply.text, tool_calls=reply.tool_calls
                )
            )
            for call in reply.tool_calls:
                with collecting() as inside:
                    # The loop runs in the field of the call that started it: a
                    # delegated search that read another field would put a passage the
                    # turn could not cite into an answer the turn signs for.
                    result = runtime.execute(call, here())
                read = _read(result, inside.untrusted)
                if read.untrusted:
                    read_untrusted()
                took(used(call, result, read, tuple(inside.steps)))
                said.append(told(result, read))
        raise ToolRefusal(OVERSPENT)

    def _offered(self, tools: tuple[Tool, ...]) -> tuple[Tool, ...]:
        """What a delegated loop may call.

        Cora's document search, and what the plugin passed. None of cora's own writing
        or stopping tools is in that set — not because they are filtered out, but
        because they are never put in. The search is described as a reader that hands
        out no numbers is offered it, which is what this loop is.

        Raises:
            ToolRefusal: A tool passed in takes the name cora's search already has.
                Refused rather than shadowed: a call would reach cora's search, and the
                plugin would watch its own tool never run.
        """
        taken = [tool.name for tool in tools if tool.name == SEARCH_TOOL_NAME]
        if taken:
            raise ToolRefusal(
                f"a tool passed to delegate is named '{SEARCH_TOOL_NAME}', which is "
                "cora's own search; rename it"
            )
        return (search_tool(self.documents, self.top_k, cites=False), *tools)

    def _registered_tools(self) -> tuple[Tool, ...]:
        return tuple(entry.value for entry in self.registered if entry.kind == TOOL)

    def _record(self, kind: str, value: Any, scope: str | None = None) -> None:
        """Keep one registration, under the scope it was made for.

        Raises:
            PluginLoadError: The scope is not a name. `None` is system-wide and is the
                one absence that means something — a blank string is a registration
                that loads and then applies to nothing, which no deployment asked for.
        """
        if scope is not None and (not isinstance(scope, str) or not scope.strip()):
            raise PluginLoadError(
                self.module, f"a {kind} was registered under a blank scope"
            )
        self.registered.append(
            Registration(module=self.module, kind=kind, value=value, scope=scope)
        )


@dataclass(frozen=True)
class _Reading:
    """The documents, searched so that the call doing the searching says it read them.

    A plugin need not delegate to reach a passage — the host hands it the index — so
    the label cannot hang off `delegate` alone. It hangs off the search, which is the
    one door every path to a passage goes through.
    """

    index: ContextSource

    def search(self, query: str, k: int) -> list[RetrievedChunk]:
        """The passages the index holds, and a note that this call has read some."""
        read_untrusted()
        return self.index.search(query, k)


def _read(result: ToolResult, read_documents: bool = False) -> Read:
    """What the loop is told, the one line its step is shown as, and where it came from.

    Passages reach a delegated loop by document name rather than by number: the numbers
    belong to the turn, and a loop that reads is not what a turn cites. So the loop can
    still say where a fact came from, and the turn can pass that on. Story 9 is where a
    delegated source earns a number of its own. Unnumbered or not, they are the user's
    documents and carry the same label a turn's own passages do.

    Args:
        read_documents: Whether the call read the user's documents somewhere inside
            itself. A tool that delegated again answers in prose, and prose built out of
            a document is the document as far as the model reading it is concerned.
    """
    if not isinstance(result.payload, Citable):
        return Read(
            body=result.render(), outcome=result.render(), untrusted=read_documents
        )
    return Read(
        body=result.payload.unnumbered(),
        outcome=result.payload.summary,
        untrusted=True,
    )


def _uncited(said: str) -> str:
    """What a delegated loop answered, with any number it wrote taken out.

    Only prose is read for citations: a fenced block is passed through as the loop wrote
    it, because a number in code is the code's own. Everywhere else the indentation, the
    blank lines and the alignment are what the outer model reads and what the reader
    opens under the call, and none of them is touched.
    """
    written: list[str] = []
    opened_with: str | None = None
    for line in said.splitlines():
        fence = FENCE.match(line)
        if fence and opened_with is None:
            opened_with = fence.group(1)
        elif fence and fence.group(1) == opened_with:
            opened_with = None
        elif opened_with is None:
            written.append(_closed_up(line))
            continue
        written.append(line)
    return "\n".join(written)


def _closed_up(line: str) -> str:
    """One line of prose with its citations removed, and the gap they left closed up.

    A number the line opened with takes the space after it, so `[1] sleep` reads
    `sleep`; the indentation and any list marker in front of it are the loop's own and
    stay. A number mid-sentence goes with the space that introduced it, so what is left
    is the sentence without it rather than the sentence re-flowed.
    """
    written = OPENED_WITH.sub(r"\1", line)
    written = UNCITED.sub("", written)
    return written if written.strip() else ""


@contextmanager
def _spending(rounds: int) -> Iterator[list[int]]:
    """The rounds this delegation may spend: a pot of its own, or the one already open.

    A nested loop joins the pot the loop above it opened, so depth spends the same
    allowance rather than a fresh one — and its own `rounds` is not honoured, because
    the outermost loop is what asked for the pot.
    """
    open_pot = _allowance.get()
    if open_pot is not None:
        yield open_pot
        return
    pot = [min(rounds, MAX_DELEGATED_ROUNDS) + 1]
    token = _allowance.set(pot)
    try:
        yield pot
    finally:
        _allowance.reset(token)
