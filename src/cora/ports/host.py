"""Cora as a plugin is handed it: what it may register, and what it may use."""

import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from cora.ports.chat_model import ChatModel
from cora.ports.context_source import ContextSource
from cora.ports.memory import Memory
from cora.ports.plugin import Tool, ValidationRule

TOOL = "tool"
RULE = "rule"
INSTRUCTIONS = "instructions"
"""What a plugin can register. A kind is a field rather than a class, so the listing,
the collision check and the log line are each written once over one list — and a fifth
kind is a method on `Host` and an entry here, not a shape anyone has to widen."""


@dataclass(frozen=True)
class Registration:
    """One thing a plugin registered, and the module that registered it.

    The module is what a refusal quotes back, because it is what the deployment typed.
    `value` is read according to `kind`, in the one place that turns registrations into
    what a turn takes.
    """

    module: str
    kind: str
    value: Any


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
    ) -> None:
        """Offer the model one more thing it can do, as `Tool` describes one."""
        ...

    def register_rule(self, rule: ValidationRule) -> None:
        """Screen what the user types, before a turn starts."""
        ...

    def register_instructions(self, instructions: str) -> None:
        """Say what this plugin is for, as a section of the model's brief."""
        ...

    @property
    def documents(self) -> ContextSource:
        """What the user uploaded, searchable as cora's own tool searches it."""
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

        The loop is offered the tools given plus cora's document search, and never a
        tool that writes or stops to ask: a delegated loop reads, and the turn around
        it is where an effect belongs. Its steps are reported under the call that ran
        it.

        Args:
            task: What the loop is being asked to do, as its first message.
            tools: What it may call, on top of searching the documents.
            rounds: How many rounds of tools it may spend.

        Raises:
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
