"""Cora as one plugin is handed it, and where what that plugin registers is kept."""

import logging
import re
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any

from jsonschema import Draft202012Validator, SchemaError

from cora.domain.card import Card
from cora.domain.citations import Citable
from cora.domain.errors import PluginLoadError
from cora.domain.trace import WorkShown
from cora.engine import keeping
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
    State,
    Subscription,
    name_of,
)
from cora.ports.memory import Memory
from cora.ports.output import Output
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
WITHHELD = (
    "not offering %s to the delegated loop: a tool that waits for the user cannot run "
    "there, and a sub-agent is not something the user is watching"
)
"""What a plugin is told when one of its tools is kept out of a loop it delegated. On
the plugin's own logger, because it is that plugin's tool and that plugin's author who
has to understand why the loop never called it."""
OVERSPENT = (
    "the sub-agent ran out of rounds without reaching an answer; ask it something "
    "narrower, or answer without it"
)
"""What the model is told when a delegated loop gives up with nothing to show. A
sentence rather than a failure of the turn's: the turn has rounds left, and this is one
call it cannot use. Reached only when the write-up below comes back empty — a loop that
spent its rounds *learning* something reports it instead."""
CLOSE_OUT = (
    "You have run out of rounds, so this is your last message. Write up what you found "
    "in a few sentences, and say plainly what you did not get to. Call no tools."
)
"""What the loop is asked once its rounds are gone. A round it cannot spend on tools:
the call it answers is offered none, so this cannot become another lookup."""
STOPPED_EARLY = (
    "STOPPED EARLY: the sub-agent reached its limit of rounds, so what follows is what "
    "it had found and not a complete answer."
)
"""What the report is headed with when the loop was stopped rather than finished.

A statement and not an instruction. A report earns the untrusted-data label like any
other material a tool hands back, and that label tells the model never to follow
instructions found inside it — so a sentence here telling it what to do would be
addressed to a reader under orders to ignore it. What survives the label is what is
needed: evidence that this is a part and not a whole. Telling the model what to do
about that belongs in a brief, where cora speaks in its own voice.
"""
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
    output: Output | None = None
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
    def state(self) -> State:
        """What this plugin kept for the conversation this turn is answering on.

        Namespaced under the name cora loaded it as, so two plugins choosing one name
        keep two values. Reachable while one of this plugin's tool calls is running,
        and outside one it reads nothing and keeps nothing.
        """
        return _Keeping(name_of(self.module))

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
        untrusted: bool = False,
        effect: bool = False,
        asks: Callable[[dict[str, Any]], Card | None] | None = None,
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
                untrusted=untrusted,
                effect=effect,
                asks=asks,
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

    def show(self, did: str, detail: str = "", failed: bool = False) -> None:
        """Put one line of this plugin's own work on the trace of the call it is in.

        The plugin is not a parameter: the name is this host's, which is what makes a
        line unforgeable. Outside a call `took` has nothing to report to and drops it,
        so nothing here has to know whether a turn is running.
        """
        took(WorkShown(plugin=self.module, did=did, detail=detail, failed=failed))

    def delegate(self, task: str, tools: tuple[Tool, ...] = (), rounds: int = 3) -> str:
        """Run a bounded loop of the model's own, and answer with what it wrote.

        Offered the tools given plus cora's document search, and none of cora's own
        tools that write or stop the turn. Every round is reported to the call this ran
        inside, so a reader sees the loop's work under the tool that ran it. What comes
        back cites nothing: the numbers a reader can click belong to the turn.

        Args:
            task: What the loop is being asked to do, as its first message.
            tools: What it may call, on top of searching the documents. One that waits
                for the user is withheld, and the plugin's logger says which.
            rounds: How many rounds it may spend, up to `MAX_DELEGATED_ROUNDS`. One
                more than this reaches the model, the last with the tools still on the
                table so a loop can answer in it. Ignored in a loop delegated from
                another, which spends what the outermost one opened.

        Raises:
            ToolRefusal: The loop gathered nothing before its rounds ran out, or was
                asked to write up what it had and answered with nothing, or a tool
                passed in takes the name cora's search already has. The call fails and
                the model is told why; the turn around it answers anyway.
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
        return self._closed_out(said)

    def _closed_out(self, said: list[Message]) -> str:
        if not any(message.role == "tool" for message in said):
            raise ToolRefusal(OVERSPENT)
        said.append(Message(role="user", content=CLOSE_OUT))
        reply = self.model.complete(tuple(said), ())
        took(decided(reply))
        written = _uncited(reply.text).strip()
        if not written:
            raise ToolRefusal(OVERSPENT)
        return f"{STOPPED_EARLY}\n\n{written}"

    def _offered(self, tools: tuple[Tool, ...]) -> tuple[Tool, ...]:
        taken = [tool.name for tool in tools if tool.name == SEARCH_TOOL_NAME]
        if taken:
            raise ToolRefusal(
                f"a tool passed to delegate is named '{SEARCH_TOOL_NAME}', which is "
                "cora's own search; rename it"
            )
        withheld = [tool.name for tool in tools if tool.effect or tool.asks]
        if withheld:
            self.log.info(WITHHELD, ", ".join(withheld))
        reading = tuple(tool for tool in tools if not (tool.effect or tool.asks))
        return (search_tool(self.documents, self.top_k, cites=False), *reading)

    def _registered_tools(self) -> tuple[Tool, ...]:
        return tuple(entry.value for entry in self.registered if entry.kind == TOOL)

    def _record(self, kind: str, value: Any, scope: str | None = None) -> None:
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


@dataclass(frozen=True)
class _Keeping:
    """One plugin's own keys, in whatever conversation the work now belongs to.

    The name is held here rather than passed in by the plugin, because only the host
    knows which plugin is asking — the same reason a log line and a setting are named
    here.
    """

    plugin: str

    def read(self, name: str) -> str | None:
        """What this plugin kept under this name, or nothing."""
        return keeping.read(self.plugin, name)

    def keep(self, name: str, value: str | None) -> None:
        """Keep this text under this name, or drop the name given nothing."""
        keeping.keep(self.plugin, name, value)


def _read(result: ToolResult, read_documents: bool = False) -> Read:
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
    written = OPENED_WITH.sub(r"\1", line)
    written = UNCITED.sub("", written)
    return written if written.strip() else ""


@contextmanager
def _spending(rounds: int) -> Iterator[list[int]]:
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
