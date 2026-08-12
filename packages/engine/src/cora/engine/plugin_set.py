from dataclasses import dataclass

from cora.domain.errors import ConfigurationError
from cora.engine.memory_tool import REMEMBER_TOOL_NAME
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME
from cora.engine.validation import (
    MAX_INPUT_CHARS,
    EmptyInputRule,
    MaxLengthRule,
    PromptInjectionRule,
)
from cora.ports.plugin import Plugin, Tool, ValidationRule

CORA_RULES: tuple[ValidationRule, ...] = (
    EmptyInputRule(),
    MaxLengthRule(MAX_INPUT_CHARS),
    PromptInjectionRule(),
)

RESERVED_TOOL_NAMES = {
    SEARCH_TOOL_NAME: "document search",
    REMEMBER_TOOL_NAME: "what the agent keeps about the user",
}


@dataclass(frozen=True)
class PluginSet:
    """The plugins cora was asked for, composed in the order they were named. Each
    travels with the module path it was loaded from, because that is what the user
    typed and what a collision has to quote back to them — `name` only words a prompt
    heading, so two plugins may share one.

    Every refusal a *combination* can earn is raised here, at construction: the
    composition root wires an already-valid set."""

    entries: tuple[tuple[str, Plugin], ...] = ()

    def __post_init__(self) -> None:
        self._reject_a_module_named_twice()
        self._reject_a_name_of_coras_own()
        self._reject_one_name_offered_twice()

    @property
    def tools(self) -> tuple[Tool, ...]:
        return tuple(tool for _, plugin in self.entries for tool in plugin.tools)

    @property
    def rules(self) -> tuple[ValidationRule, ...]:
        offered = tuple(
            rule for _, plugin in self.entries for rule in plugin.validation_rules
        )
        return CORA_RULES + offered

    @property
    def system_prompt(self) -> str:
        return "\n\n".join(
            plugin.system_prompt.strip()
            for _, plugin in self.entries
            if plugin.system_prompt.strip()
        )

    @property
    def grounding(self) -> str:
        return "\n\n".join(
            plugin.grounding.strip()
            for _, plugin in self.entries
            if plugin.grounding.strip()
        )

    def _reject_a_module_named_twice(self) -> None:
        seen: set[str] = set()
        for module, _ in self.entries:
            if module in seen:
                raise ConfigurationError(
                    f"'{module}' is listed twice. Name each plugin once."
                )
            seen.add(module)

    def _reject_a_name_of_coras_own(self) -> None:
        for module, plugin in self.entries:
            for tool in plugin.tools:
                if tool.name in RESERVED_TOOL_NAMES:
                    raise ConfigurationError(
                        f"'{module}' offers a tool named '{tool.name}', and that name "
                        f"belongs to {RESERVED_TOOL_NAMES[tool.name]}."
                    )

    def _reject_one_name_offered_twice(self) -> None:
        offered_by: dict[str, str] = {}
        for module, plugin in self.entries:
            for tool in plugin.tools:
                first = offered_by.get(tool.name)
                if first is not None:
                    raise ConfigurationError(
                        f"'{first}' and '{module}' both offer a tool named "
                        f"'{tool.name}'. Load one of them, or rename the tool."
                    )
                offered_by[tool.name] = module
