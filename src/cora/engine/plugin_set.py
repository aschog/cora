"""What the plugins registered, as one list — and what they may not register."""

from dataclasses import dataclass

from cora.domain.errors import ConfigurationError
from cora.engine.ask_tool import ASK_TOOL_NAME
from cora.engine.memory_tool import REMEMBER_TOOL_NAME
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME
from cora.engine.validation import MAX_INPUT_CHARS, EmptyInputRule, MaxLengthRule
from cora.ports.host import INSTRUCTIONS, RULE, TOOL, Registration
from cora.ports.plugin import Tool, ValidationRule

CORA_RULES: tuple[ValidationRule, ...] = (
    EmptyInputRule(),
    MaxLengthRule(MAX_INPUT_CHARS),
)
"""What cora asks of any input, whatever it was asked to be. Screening for injection is
not here: it is a plugin, and so something a deployment adds."""

RESERVED_TOOL_NAMES = {
    SEARCH_TOOL_NAME: "document search",
    REMEMBER_TOOL_NAME: "what the agent keeps about the user",
    ASK_TOOL_NAME: "stopping to ask the user",
}


@dataclass(frozen=True)
class Registry:
    """Everything the plugins registered, in the order they registered it.

    One list rather than one field per kind: the listing, the collision check and the
    log line are each written once, and a fifth kind of contribution adds an entry
    rather than widening a shape. Each entry carries the module that made it, because
    that is what a refusal quotes back to the deployment.

    Every refusal a *combination* can earn is raised here, at construction: the
    composition root wires an already-valid registry.
    """

    entries: tuple[Registration, ...] = ()

    def __post_init__(self) -> None:
        """Refuse a registry that cannot be composed, before anything is wired to it.

        Raises:
            ConfigurationError: A plugin registered a tool name that is cora's own, or
                two plugins registered the same one.
        """
        self._reject_a_name_of_coras_own()
        self._reject_one_name_registered_twice()

    @property
    def modules(self) -> tuple[str, ...]:
        """Every module that registered anything, in the order it first did."""
        found: list[str] = []
        for entry in self.entries:
            if entry.module not in found:
                found.append(entry.module)
        return tuple(found)

    @property
    def tools(self) -> tuple[Tool, ...]:
        """Every tool registered, in the order it was registered."""
        return tuple(entry.value for entry in self._of(TOOL))

    @property
    def rules(self) -> tuple[ValidationRule, ...]:
        """Cora's own rules first, then the registered ones in registration order.

        The order is the order they run in, and cora's come first so a plugin's rule is
        never handed something cora would have refused outright.
        """
        return CORA_RULES + tuple(entry.value for entry in self._of(RULE))

    @property
    def instructions(self) -> str:
        """One section per module that registered any, headed by the module's own name.

        Headed by cora rather than by the plugin: a section says which plugin wrote it,
        and no plugin can put another's name on its own instructions.
        """
        return "\n\n".join(
            f"## {_heading(entry.module)}\n{entry.value.strip()}"
            for entry in self._of(INSTRUCTIONS)
            if entry.value.strip()
        )

    def _of(self, kind: str) -> tuple[Registration, ...]:
        return tuple(entry for entry in self.entries if entry.kind == kind)

    def _reject_a_name_of_coras_own(self) -> None:
        for entry in self._of(TOOL):
            if entry.value.name in RESERVED_TOOL_NAMES:
                raise ConfigurationError(
                    f"'{entry.module}' registers a tool named '{entry.value.name}', "
                    f"and that name belongs to {RESERVED_TOOL_NAMES[entry.value.name]}."
                )

    def _reject_one_name_registered_twice(self) -> None:
        registered_by: dict[str, str] = {}
        for entry in self._of(TOOL):
            first = registered_by.get(entry.value.name)
            if first is not None:
                raise ConfigurationError(
                    f"'{first}' and '{entry.module}' both register a tool named "
                    f"'{entry.value.name}'. Load one of them, or rename the tool."
                )
            registered_by[entry.value.name] = entry.module


def _heading(module: str) -> str:
    """The name a plugin's section of the brief is headed by, taken from its module."""
    return module.rsplit(".", 1)[-1].replace("_", " ").strip().capitalize()
