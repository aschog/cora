"""What the plugins registered, as one list — and what of it a turn takes."""

from dataclasses import dataclass

from cora.domain.errors import ConfigurationError
from cora.engine.ask_tool import ASK_TOOL_NAME
from cora.engine.memory_tool import REMEMBER_TOOL_NAME
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME
from cora.engine.validation import CORA
from cora.ports.host import HANDLER, INSTRUCTIONS, SCREENING, TOOL, Registration
from cora.ports.plugin import Tool

RESERVED_TOOL_NAMES = {
    SEARCH_TOOL_NAME: "document search",
    REMEMBER_TOOL_NAME: "what the agent keeps about the user",
    ASK_TOOL_NAME: "stopping to ask the user",
}


def applies(entry: Registration, scopes: frozenset[str]) -> bool:
    """Whether a registration takes part in a turn running under these scopes.

    One filter for handlers, tools and instructions alike: a registration carrying no
    scope applies everywhere, and one carrying a name applies where that name is
    active. "Cannot be scoped away" is this and nothing else — a system-wide screen is
    unremovable because no scope is ever asked about it.
    """
    return entry.scope is None or entry.scope in scopes


@dataclass(frozen=True)
class Registry:
    """Everything registered, in the order it was registered — cora's own included.

    One list rather than one field per kind: the listing, the collision check and the
    log line are each written once, and a fifth kind of contribution adds an entry
    rather than widening a shape. Each entry carries the module that made it, because
    that is what a refusal quotes back to the deployment, and the scope it applies in.

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

    def tools(self, scopes: frozenset[str] = frozenset()) -> tuple[Tool, ...]:
        """Every tool that applies to a turn under these scopes, as registered."""
        return tuple(entry.value for entry in self._of(TOOL) if applies(entry, scopes))

    def instructions(self, scopes: frozenset[str] = frozenset()) -> str:
        """One section per module that registered any that applies, under its own name.

        Headed by cora rather than by the plugin: a section says which plugin wrote it,
        and no plugin can put another's name on its own instructions.
        """
        return "\n\n".join(
            f"## {_heading(entry.module)}\n{entry.value.strip()}"
            for entry in self._of(INSTRUCTIONS)
            if applies(entry, scopes) and entry.value.strip()
        )

    def outline(self, scope: str) -> str:
        """One sentence saying what a scope is for, taken off its own instructions.

        What a router is given to choose between, and what an option on the card that
        asks the user says under the name. The first sentence a plugin wrote, because a
        persona opens by saying what it answers — and a scope nobody wrote instructions
        for is described by its name alone.
        """
        for entry in self._of(INSTRUCTIONS):
            if entry.scope == scope and entry.value.strip():
                return _first_sentence(entry.value)
        return ""

    def handlers(
        self, event: str, scopes: frozenset[str] = frozenset()
    ) -> tuple[Registration, ...]:
        """What is subscribed to one event and applies here, in the order it ran in.

        Registration order, which is load order, which is cora's own first: a plugin's
        screen is never handed a question cora would have refused outright.
        """
        return tuple(
            entry
            for entry in self._of(HANDLER)
            if entry.value.event == event and applies(entry, scopes)
        )

    def screened_by_a_plugin(self) -> bool:
        """Whether anything but cora itself screens what the user types."""
        return any(
            entry.value.event == SCREENING and entry.module != CORA
            for entry in self._of(HANDLER)
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


def _first_sentence(instructions: str) -> str:
    """The opening sentence, unwrapped.

    A line break is where the author's editor wrapped and says nothing about where the
    thought ends, so the paragraph is read whole and cut at the first full stop. A
    paragraph with none is one sentence that has not ended.
    """
    opening = instructions.strip().split("\n\n")[0]
    said = " ".join(word for word in opening.split())
    ended = said.find(". ")
    return said if ended < 0 else said[: ended + 1]


def _heading(module: str) -> str:
    """The name a plugin's section of the brief is headed by, taken from its module."""
    return module.rsplit(".", 1)[-1].replace("_", " ").strip().capitalize()
