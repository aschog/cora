"""Cora as one plugin is handed it, and where what that plugin registers is kept."""

import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from jsonschema import Draft202012Validator, SchemaError

from cora.domain.citations import Citable
from cora.domain.errors import PluginLoadError, ToolLoopLimitError
from cora.domain.trace import ModelDecision, ToolUse
from cora.engine.nesting import took
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
MAY_NOT_DELEGATE = ("remember", "ask_user")
"""A delegated loop reads and never acts, so the tools that write what cora keeps or
stop the turn to ask are not offered to one. The turn around it is where an effect
belongs, and it is where the gate already is."""


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

        Offered the tools given plus cora's document search, and never one that writes
        or stops to ask. Every round is reported to the call this ran inside, so a
        reader sees the loop's work under the tool that ran it.

        Args:
            task: What the loop is being asked to do, as its first message.
            tools: What it may call, on top of searching the documents.
            rounds: How many rounds of tools it may spend.

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
        for _ in range(rounds + 1):
            reply = self.model.complete(tuple(said), offered)
            took(
                ModelDecision(
                    detail="" if reply.is_final else reply.text,
                    tools=tuple(call.name for call in reply.tool_calls),
                )
            )
            if reply.is_final:
                return reply.text
            said.append(
                Message(
                    role="assistant", content=reply.text, tool_calls=reply.tool_calls
                )
            )
            for call in reply.tool_calls:
                result = runtime.execute(call)
                read, outcome = _read(result)
                took(
                    ToolUse(
                        name=call.name,
                        arguments=call.arguments,
                        outcome=outcome,
                        detail=read,
                        failed=result.error is not None,
                    )
                )
                said.append(
                    Message(role="tool", content=read, tool_call_id=result.call_id)
                )
        raise ToolLoopLimitError

    def _offered(self, tools: tuple[Tool, ...]) -> tuple[Tool, ...]:
        """What a delegated loop may call: reading tools, cora's search among them."""
        asked = tuple(tool for tool in tools if tool.name not in MAY_NOT_DELEGATE)
        return (search_tool(self.documents, self.top_k), *asked)

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
