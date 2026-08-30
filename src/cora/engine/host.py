"""Cora as one plugin is handed it, and where what that plugin registers is kept."""

import logging
import re
from collections.abc import Callable, Mapping
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
    "offered. Be brief and concrete, and answer from what the tools return."
)
MAX_DELEGATED_ROUNDS = 5
"""The most rounds a delegated loop may spend, whatever it asks for. The budget is the
host's rather than the plugin's: one tool call that asked for ten thousand rounds would
spend a deployment's bill, and a turn may make one such call per round of its own."""
UNCITED = re.compile(rf"\s*{CITATION_RUN.pattern}")
"""What a delegated loop's answer is stripped of, by the rule the page draws buttons
with. The numbers belong to the turn, and a loop handing itself `[1]` would collide with
the `[1]` the reader has already been shown — pointing a button at another document."""


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
                `MAX_DELEGATED_ROUNDS`.

        Raises:
            ToolLoopLimitError: The loop spent its rounds without reaching an answer.
            LlmError: The model gave back nothing usable.
        """
        offered = self._offered(tools)
        spend = min(rounds, MAX_DELEGATED_ROUNDS)
        runtime = ToolRuntime(tools=offered)
        said: list[Message] = [
            Message(role="system", content=DELEGATE_BRIEF),
            Message(role="user", content=task),
        ]
        for _ in range(spend + 1):
            reply = self.model.complete(tuple(said), offered)
            took(
                ModelDecision(
                    detail="" if reply.is_final else reply.text,
                    tools=tuple(call.name for call in reply.tool_calls),
                )
            )
            if reply.is_final:
                return UNCITED.sub("", reply.text).strip()
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

    Passages reach a delegated loop as text rather than as numbered citations: the
    numbers belong to the turn, and a loop that reads is not what a turn cites. Story 9
    is where a delegated source earns a number of its own.
    """
    if not isinstance(result.payload, Citable):
        return result.render(), result.render()
    return result.payload.register(()).text, result.payload.summary
