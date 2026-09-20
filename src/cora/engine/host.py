"""Cora as one plugin is handed it, and where what that plugin registers is kept."""

import logging
import os
import pathlib
import re
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, overload

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
from cora.ports.context_source import ContextSource, Document
from cora.ports.host import (
    HANDLER,
    INSTRUCTIONS,
    PAGE,
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
from cora.ports.store import Kept, Store

DELEGATE_BRIEF = (
    "You are answering one question on behalf of an assistant, using the tools you are "
    "offered. Be brief and concrete, and answer from what the tools return. Name the "
    "document a fact came from in your own words — never write a citation number, "
    "because the numbers belong to the assistant and not to you."
)
ANSWER_TOOL_NAME = "answer"
ANSWER_TOOL_DESCRIPTION = (
    "Answer with the fields this takes, and stop. This is the only answer that is "
    "read: prose is not, and nothing else is called afterwards."
)
SHAPED_BRIEF = (
    "\n\nAnswer only by calling `answer` with the fields it takes. Prose is not "
    "read, so an answer written as prose is an answer nobody receives."
)
TAKEN = "a tool passed to delegate is named '{name}', which is cora's own; rename it"
UNSHAPED = (
    "the sub-agent wrote prose where it was given a shape to answer in, so there is no "
    "value to read; ask it again, or answer without it"
)
NOT_A_SHAPE = (
    "the shape passed to delegate is not valid JSON Schema, so nothing could be held "
    "to it"
)
REQUIRES_NOTHING = (
    "the shape passed to delegate requires nothing of an answer, so an empty one would "
    "satisfy it; name what it must have in `required`"
)
MAX_DELEGATED_ROUNDS = 5
WITHHELD = (
    "not offering %s to the delegated loop: a tool that waits for the user cannot run "
    "there, and a sub-agent is not something the user is watching"
)
OVERSPENT = (
    "the sub-agent ran out of rounds without reaching an answer; ask it something "
    "narrower, or answer without it"
)
CLOSE_OUT = (
    "You have run out of rounds, so this is your last message. Write up what you found "
    "in a few sentences, and say plainly what you did not get to. Call no tools."
)
STOPPED_EARLY = (
    "STOPPED EARLY: the sub-agent reached its limit of rounds, so what follows is what "
    "it had found and not a complete answer."
)
_allowance: ContextVar[list[int] | None] = ContextVar("_allowance", default=None)
CITED = r"(?:\[\d+\])+"
OPENS = r"=([{<>|&^~/\\+"
UNCITED = re.compile(rf"(?<=[^\s{OPENS}])[ \t]+{CITED}")
OPENED_WITH = re.compile(rf"^([ \t]*(?:[-*+][ \t]+)?){CITED}[ \t]*")
FENCE = re.compile(r"^[ \t]*(```|~~~)")


PLUGIN_LOGGER = "cora.plugin"


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
    kept: Store | None = None
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
    def store(self) -> Kept | None:
        """This plugin's own store, or nothing where the deployment keeps none.

        Namespaced under the name cora loaded it as, so two plugins choosing one name
        keep two values.
        """
        if self.kept is None:
            return None
        return _KeepingForGood(self.kept, name_of(self.module))

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

    def register_page(self, directory: str | os.PathLike[str], *, scope: str) -> None:
        """Bring one field its own page, as a directory to serve whole.

        What is on disk is not checked here: a page is read at the request, and a
        directory that is not there then costs that path a refusal rather than the
        composition every other request also needs.

        Raises:
            PluginLoadError: No field was named, or this plugin already brought that
                field a page.
        """
        if scope is None:
            raise PluginLoadError(
                self.module, "a page was registered under no field to draw it in"
            )
        if any(entry.scope == scope for entry in self._of(PAGE)):
            raise PluginLoadError(
                self.module, f"a page for '{scope}' was registered twice"
            )
        self._record(PAGE, pathlib.Path(directory), scope)

    def show(self, did: str, detail: str = "", failed: bool = False) -> None:
        """Put one line of this plugin's own work on the trace of the call it is in.

        The plugin is not a parameter: the name is this host's, which is what makes a
        line unforgeable. Outside a call `took` has nothing to report to and drops it,
        so nothing here has to know whether a turn is running.
        """
        took(WorkShown(plugin=self.module, did=did, detail=detail, failed=failed))

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
            shape: JSON Schema the answer must satisfy. Given one, the loop answers by
                calling a tool of that shape and this hands back the validated value
                rather than prose. It must require something: an answer satisfying a
                shape that requires nothing is an empty one.

        Raises:
            ToolRefusal: The loop gathered nothing before its rounds ran out, or was
                asked to write up what it had and answered with nothing, or a tool
                passed in takes a name of cora's own. With a shape: the shape is not one
                anything could be held to, or the loop wrote prose instead of answering
                in it, or its rounds ran out. The call fails and the model is told why;
                the turn around it answers anyway.
            LlmError: The model gave back nothing usable.
        """
        if shape is not None:
            _checked(shape)
        offered = self._offered(tools, shape)
        runtime = ToolRuntime(tools=offered)
        said: list[Message] = [
            Message(
                role="system",
                content=DELEGATE_BRIEF + (SHAPED_BRIEF if shape is not None else ""),
            ),
            Message(role="user", content=task),
        ]
        with _spending(rounds) as left:
            return self._rounds(said, offered, runtime, left, shape is not None)

    def _rounds(
        self,
        said: list[Message],
        offered: tuple[Tool, ...],
        runtime: ToolRuntime,
        left: list[int],
        shaped: bool = False,
    ) -> str | dict[str, Any]:
        while left[0] > 0:
            left[0] -= 1
            reply = self.model.complete(tuple(said), offered)
            took(decided(reply))
            if reply.is_final:
                if shaped:
                    raise ToolRefusal(UNSHAPED)
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
                if shaped and call.name == ANSWER_TOOL_NAME and result.error is None:
                    return _uncited_value(result.payload)
                said.append(told(result, read))
        if shaped:
            raise ToolRefusal(OVERSPENT)
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

    def _offered(
        self, tools: tuple[Tool, ...], shape: Mapping[str, Any] | None = None
    ) -> tuple[Tool, ...]:
        own = {SEARCH_TOOL_NAME} | ({ANSWER_TOOL_NAME} if shape is not None else set())
        taken = [tool.name for tool in tools if tool.name in own]
        if taken:
            raise ToolRefusal(TAKEN.format(name=taken[0]))
        withheld = [tool.name for tool in tools if tool.effect or tool.asks]
        if withheld:
            self.log.info(WITHHELD, ", ".join(withheld))
        reading = tuple(tool for tool in tools if not (tool.effect or tool.asks))
        answering = (_answering(shape),) if shape is not None else ()
        return (
            search_tool(self.documents, self.top_k, cites=False),
            *reading,
            *answering,
        )

    def _registered_tools(self) -> tuple[Tool, ...]:
        return tuple(entry.value for entry in self._of(TOOL))

    def _of(self, kind: str) -> tuple[Registration, ...]:
        return tuple(entry for entry in self.registered if entry.kind == kind)

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

    def all(self) -> list[Document]:
        """The documents the index holds, and a note that this call has read them."""
        read_untrusted()
        return self.index.all()


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


@dataclass(frozen=True)
class _KeepingForGood:
    """One plugin's row of the deployment's store, with the plugin already filled in.

    The same reason `_Keeping` holds the name: only the host knows which plugin is
    asking, and a plugin naming itself could name another.
    """

    kept: Store
    plugin: str

    def read(self, name: str) -> str | None:
        """What this plugin kept under this name, or nothing."""
        return self.kept.read(self.plugin, name)

    def keep(self, name: str, value: str | None) -> None:
        """Keep this text under this name, or drop the name given nothing."""
        self.kept.keep(self.plugin, name, value)


def _checked(shape: Mapping[str, Any]) -> None:
    try:
        Draft202012Validator.check_schema(shape)
    except SchemaError as invalid:
        raise ToolRefusal(NOT_A_SHAPE) from invalid
    if not shape.get("required"):
        raise ToolRefusal(REQUIRES_NOTHING)


def _answering(shape: Mapping[str, Any]) -> Tool:
    return Tool(
        name=ANSWER_TOOL_NAME,
        description=ANSWER_TOOL_DESCRIPTION,
        parameter_schema=dict(shape),
        run=lambda **given: given,
    )


def _uncited_value(value: Any) -> Any:
    if isinstance(value, str):
        return _uncited(value)
    if isinstance(value, dict):
        return {key: _uncited_value(each) for key, each in value.items()}
    if isinstance(value, list):
        return [_uncited_value(each) for each in value]
    return value


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
