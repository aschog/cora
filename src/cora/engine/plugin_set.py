"""What the plugins registered, as one list — and what of it a turn takes."""

import pathlib
from collections.abc import Callable
from dataclasses import dataclass

from cora.domain.errors import ConfigurationError
from cora.engine.ask_tool import ASK_FOR_TOOL_NAME, ASK_TOOL_NAME
from cora.engine.memory_tool import REMEMBER_TOOL_NAME
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME
from cora.engine.validation import CORA
from cora.ports.host import (
    HANDLER,
    HAS_AN_EFFECT,
    INSTRUCTIONS,
    PAGE,
    SCREENING,
    TOOL,
    Contributed,
    Extension,
    Listed,
    Registration,
    name_of,
)
from cora.ports.plugin import Tool

RESERVED_TOOL_NAMES = {
    SEARCH_TOOL_NAME: "document search",
    REMEMBER_TOOL_NAME: "what the agent keeps about the user",
    ASK_TOOL_NAME: "stopping to ask the user",
    ASK_FOR_TOOL_NAME: "stopping to ask the user for values",
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
class Unique:
    """One thing a registry may hold only one of per key, and what to say of a second.

    A rule as a value rather than a method: the next kind that must be unique — an
    instructions block per field, a handler per event — is an entry below rather than a
    fourth loop that says the same thing a fourth way.
    """

    kind: str
    key: Callable[[Registration], str]
    said: str


ONE_EACH = (
    Unique(
        kind=TOOL,
        key=lambda entry: str(entry.value.name),
        said=(
            "'{first}' and '{second}' both register a tool named '{named}'. "
            "Load one of them, or rename the tool."
        ),
    ),
    Unique(
        kind=PAGE,
        key=lambda entry: str(entry.scope),
        said=(
            "'{first}' and '{second}' both bring the page of '{named}'. "
            "Load one of them."
        ),
    ),
)


@dataclass(frozen=True)
class Registry:
    """Everything registered, in the order it was registered — cora's own included.

    One list rather than one field per kind: the listing, the collision check and the
    log line are each written once, and a fourth kind of contribution adds an entry
    rather than widening a shape. Each entry carries the module that made it, because
    that is what a refusal quotes back to the deployment, and the scope it applies in.

    Every refusal a *combination* can earn is raised here, at construction: the
    composition root wires an already-valid registry.
    """

    entries: tuple[Registration, ...] = ()

    def __post_init__(self) -> None:
        """Refuse a registry that cannot be composed, before anything is wired to it.

        Raises:
            ConfigurationError: A plugin registered a tool name that is cora's own,
                two plugins registered the same one, or two brought one field's page.
        """
        self._reject_a_name_of_coras_own()
        for unique in ONE_EACH:
            self._reject_two_of_one(unique)

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
        """What a scope is for, in the words its own instructions open with.

        What a router is given to choose between, and what an option on the card that
        asks the user says under the name. The opening paragraph, because a persona
        opens by saying what it answers — and a scope nobody wrote instructions for is
        described by its name alone.
        """
        for entry in self._of(INSTRUCTIONS):
            if entry.scope == scope and entry.value.strip():
                return _opening(entry.value)
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

    def listing(self, plugins: tuple[Extension, ...]) -> tuple[Listed, ...]:
        """What each of these plugins registered, in the order they were loaded.

        A projection of the registrations already held rather than a second record, so
        a listing cannot drift from the app it describes. Driven by the plugins given:
        cora's own registrations are not a plugin's and are not listed, and a plugin
        that registered nothing is listed with nothing under it — it is the one an
        operator most needs to see.
        """
        return tuple(
            Listed(
                name=name_of(plugin.module),
                source=plugin.source,
                contributions=tuple(
                    _contributed(entry)
                    for entry in self.entries
                    if entry.module == plugin.module
                ),
            )
            for plugin in plugins
        )

    def pages(self) -> dict[str, pathlib.Path]:
        """The directory to serve for each field a plugin brought a page for.

        A field has one page, which `__post_init__` is what makes true, so a mapping is
        the whole of it — and the one thing about a page that a frontend is handed.
        """
        return {
            str(entry.scope): entry.value
            for entry in self._of(PAGE)
            if entry.scope is not None
        }

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

    def _reject_two_of_one(self, unique: "Unique") -> None:
        first_by: dict[str, str] = {}
        for entry in self._of(unique.kind):
            named = unique.key(entry)
            first = first_by.get(named)
            if first is not None:
                raise ConfigurationError(
                    unique.said.format(first=first, second=entry.module, named=named)
                )
            first_by[named] = entry.module


def _contributed(entry: Registration) -> Contributed:
    named = {
        TOOL: lambda value: str(value.name),
        HANDLER: lambda value: str(value.event),
    }.get(entry.kind, lambda value: "")
    noted = {TOOL: lambda value: HAS_AN_EFFECT if value.effect else ""}.get(
        entry.kind, lambda value: ""
    )
    return Contributed(
        kind=entry.kind,
        name=named(entry.value),
        scope=entry.scope,
        note=noted(entry.value),
    )


def _opening(instructions: str) -> str:
    return " ".join(instructions.strip().split("\n\n")[0].split())


def _heading(module: str) -> str:
    return name_of(module).replace("_", " ").strip().capitalize()
