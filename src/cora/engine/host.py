"""Cora as one plugin is handed it, and where what that plugin registers is kept."""

import logging
import re
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any

from jsonschema import Draft202012Validator, SchemaError

from cora.domain.citations import CITATION_RUN, Citable
from cora.domain.errors import PluginLoadError, ToolLoopLimitError
from cora.domain.trace import ModelDecision, ToolUse
from cora.engine.nesting import collecting, took
from cora.engine.retrieval_tool import search_tool
from cora.engine.tool_runtime import ToolRuntime
from cora.ports.chat_model import ChatModel, Message
from cora.ports.context_source import ContextSource
from cora.ports.host import INSTRUCTIONS, RULE, TOOL, Registration
from cora.ports.memory import Memory
from cora.ports.plugin import Tool, ToolResult, ValidationRule

DELEGATE_BRIEF = (
    "You are answering one question on behalf of an assistant, using the tools you are "
    "offered. Be brief and concrete, and answer from what the tools return. Name the "
    "document a fact came from in your own words — never write a citation number, "
    "because the numbers belong to the assistant and not to you."
)
MAX_DELEGATED_ROUNDS = 5
"""The most rounds a delegated loop may spend, whatever it asks for. The budget is the
host's rather than the plugin's: one tool call that asked for ten thousand rounds would
spend a deployment's bill, and a turn may make one such call per round of its own."""
_allowance: ContextVar[list[int] | None] = ContextVar("_allowance", default=None)
"""What is left of the rounds this delegation may spend, shared by every loop under it.

A delegated loop may call a tool that delegates again, and a fresh budget per level
would make depth a way of asking for more — four levels of five rounds is a thousand
model calls from one tool call. The outermost loop opens the pot and everything inside
it spends the same one, so a tool call costs what the host allows however deep the
plugin goes."""
UNCITED = re.compile(CITATION_RUN.pattern)
"""What a delegated loop's answer is stripped of, should it write a number anyway.
Stricter than the rule the page draws buttons by: the page leaves a number the turn
never handed out as plain text, while here any bracketed number goes, because a loop has
none to give. The lines around it are left as the loop wrote them."""
OPENED_WITH = re.compile(rf"^([ \t]*){CITATION_RUN.pattern}[ \t]*")
"""A number the line opened with, and the space it left behind. Whatever indentation
stood in front of it is the loop's own and is handed back untouched."""
TIGHTENED = (
    (re.compile(r"(?<=\S)[ \t]{2,}"), " "),
    (re.compile(r"[ \t]+([.,;:])"), r"\1"),
)
"""The residue of taking a number out mid-sentence: two spaces where one belongs, or a
space before the stop that followed the number. Never leading whitespace, which is the
loop's own indentation and none of cora's business."""


@dataclass
class PluginHost:
    """What one plugin's `extend` is called with, and what it registered afterwards.

    One host per plugin, so a log line and a setting are named for the plugin that read
    them, and so a registration knows which module made it. The ports are cora's own:
    a plugin searching the documents searches the index the uploads went into.
    """

    module: str
    documents: ContextSource
    model: ChatModel
    memory: Memory | None = None
    settings: Mapping[str, str] = field(default_factory=dict)
    top_k: int = 5
    registered: list[Registration] = field(default_factory=list)

    @property
    def log(self) -> logging.Logger:
        """A logger named for this plugin, so its lines say which plugin wrote them."""
        return logging.getLogger(self.module)

    def register_tool(
        self,
        *,
        name: str,
        description: str,
        parameter_schema: dict[str, Any],
        run: Callable[..., Any],
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
        )

    def register_rule(self, rule: ValidationRule) -> None:
        """Screen what the user types, before a turn starts."""
        self._record(RULE, rule)

    def register_instructions(self, instructions: str) -> None:
        """Say what this plugin is for, as a section of the model's brief."""
        self._record(INSTRUCTIONS, instructions)

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
            ToolLoopLimitError: The loop spent its rounds without reaching an answer.
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
        """One delegated loop, spending the allowance the outermost one opened."""
        while left[0] > 0:
            left[0] -= 1
            reply = self.model.complete(tuple(said), offered)
            took(
                ModelDecision(
                    detail="" if reply.is_final else reply.text,
                    tools=tuple(call.name for call in reply.tool_calls),
                )
            )
            if reply.is_final:
                return _uncited(reply.text)
            said.append(
                Message(
                    role="assistant", content=reply.text, tool_calls=reply.tool_calls
                )
            )
            for call in reply.tool_calls:
                with collecting() as inside:
                    result = runtime.execute(call)
                read, outcome = _read(result)
                took(
                    ToolUse(
                        name=call.name,
                        arguments=call.arguments,
                        outcome=outcome,
                        detail=read,
                        failed=result.error is not None,
                        steps=tuple(inside),
                    )
                )
                said.append(
                    Message(role="tool", content=read, tool_call_id=result.call_id)
                )
        raise ToolLoopLimitError

    def _offered(self, tools: tuple[Tool, ...]) -> tuple[Tool, ...]:
        """What a delegated loop may call.

        Cora's document search, and what the plugin passed. None of cora's own writing
        or stopping tools is in that set — not because they are filtered out, but
        because they are never put in.
        """
        return (search_tool(self.documents, self.top_k), *tools)

    def _registered_tools(self) -> tuple[Tool, ...]:
        return tuple(entry.value for entry in self.registered if entry.kind == TOOL)

    def _record(self, kind: str, value: Any) -> None:
        self.registered.append(Registration(module=self.module, kind=kind, value=value))


def _read(result: ToolResult) -> tuple[str, str]:
    """What the loop is told, and the one line its step is shown as.

    Passages reach a delegated loop by document name rather than by number: the numbers
    belong to the turn, and a loop that reads is not what a turn cites. So the loop can
    still say where a fact came from, and the turn can pass that on. Story 9 is where a
    delegated source earns a number of its own.
    """
    if not isinstance(result.payload, Citable):
        return result.render(), result.render()
    return result.payload.unnumbered(), result.payload.summary


def _uncited(said: str) -> str:
    """What a delegated loop answered, with any number it wrote taken out.

    Only a line a number came out of is touched, and only to close the gap it left: the
    indentation, the blank lines and the fenced blocks the loop wrote are what the outer
    model reads and what the reader opens under the call.
    """
    return "\n".join(_closed_up(line) for line in said.splitlines())


def _closed_up(line: str) -> str:
    """One line with its citations removed, and the space they left closed up.

    A number the line opened with takes the space after it, so `[1] sleep` reads
    `sleep`; the indentation in front of it is the loop's own and stays. A number
    mid-sentence leaves the two spaces around it as one.
    """
    written = OPENED_WITH.sub(r"\1", line)
    written = UNCITED.sub("", written)
    if written == line:
        return line
    for pattern, replacement in TIGHTENED:
        written = pattern.sub(replacement, written)
    return written.rstrip() if written.strip() else ""


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
