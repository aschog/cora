import pytest

from cora.domain.errors import ConfigurationError
from cora.engine.plugin_set import RESERVED_TOOL_NAMES, Registry
from cora.engine.validation import CORA
from cora.ports.host import (
    BRIEFING,
    HANDLER,
    INSTRUCTIONS,
    SCREENING,
    TOOL,
    Registration,
    Subscription,
)
from fixture_plugins import make_tool, refuses_containing

FITNESS = "cora.plugins.fitness"
SECURITY = "cora.plugins.security"
COACHING = frozenset({"fitness"})


def _registered(
    module: str, kind: str, value: object, scope: str | None = None
) -> Registration:
    return Registration(module=module, kind=kind, value=value, scope=scope)


def _subscribed(module: str, event: str, scope: str | None = None) -> Registration:
    return _registered(
        module,
        HANDLER,
        Subscription(event=event, handle=refuses_containing("no")),
        scope,
    )


def test_an_empty_registry_offers_nothing_at_all() -> None:
    empty = Registry()

    assert empty.tools() == ()
    assert empty.handlers(SCREENING) == ()
    assert empty.instructions() == ""


def test_the_registered_tools_are_offered_in_registration_order() -> None:
    registry = Registry(
        (
            _registered(FITNESS, TOOL, make_tool("bmi")),
            _registered(SECURITY, TOOL, make_tool("tdee")),
            _registered(SECURITY, TOOL, make_tool("macros")),
        )
    )

    assert [tool.name for tool in registry.tools()] == ["bmi", "tdee", "macros"]


def test_the_handlers_of_one_event_come_back_in_registration_order() -> None:
    """Which is load order, which is cora's own first: a plugin's screen is never
    handed a question cora would have refused outright."""
    registry = Registry(
        (
            _subscribed(CORA, SCREENING),
            _subscribed(SECURITY, SCREENING),
            _subscribed(FITNESS, BRIEFING),
        )
    )

    assert [entry.module for entry in registry.handlers(SCREENING)] == [CORA, SECURITY]
    assert [entry.module for entry in registry.handlers(BRIEFING)] == [FITNESS]


def test_a_scoped_registration_applies_only_where_its_scope_is_active() -> None:
    registry = Registry(
        (
            _registered(FITNESS, TOOL, make_tool("bmi"), scope="fitness"),
            _registered(SECURITY, TOOL, make_tool("scan")),
            _subscribed(FITNESS, SCREENING, scope="fitness"),
            _subscribed(SECURITY, SCREENING),
            _registered(FITNESS, INSTRUCTIONS, "Be a coach.", scope="fitness"),
        )
    )

    assert [tool.name for tool in registry.tools()] == ["scan"]
    assert [tool.name for tool in registry.tools(COACHING)] == ["bmi", "scan"]
    assert [entry.module for entry in registry.handlers(SCREENING)] == [SECURITY]
    assert registry.instructions() == ""
    assert "Be a coach." in registry.instructions(COACHING)


def test_a_plugin_is_what_screens_beyond_coras_own() -> None:
    assert not Registry((_subscribed(CORA, SCREENING),)).screened_by_a_plugin()
    assert Registry((_subscribed(SECURITY, SCREENING),)).screened_by_a_plugin()


def test_two_plugins_registering_one_tool_name_is_a_config_error() -> None:
    clash = make_tool("bmi")

    with pytest.raises(ConfigurationError) as excinfo:
        Registry(
            (_registered(FITNESS, TOOL, clash), _registered(SECURITY, TOOL, clash))
        )

    message = excinfo.value.user_message
    assert FITNESS in message
    assert SECURITY in message
    assert "bmi" in message


@pytest.mark.parametrize("reserved", sorted(RESERVED_TOOL_NAMES))
def test_a_plugin_taking_a_name_of_coras_own_is_a_config_error(reserved: str) -> None:
    with pytest.raises(ConfigurationError) as excinfo:
        Registry((_registered(FITNESS, TOOL, make_tool(reserved)),))

    assert FITNESS in excinfo.value.user_message
    assert reserved in excinfo.value.user_message


def test_two_plugins_are_two_sections_headed_by_their_modules() -> None:
    """A section says which plugin wrote it, and cora heads it rather than the plugin:
    no plugin can put another's name on its own instructions."""
    registry = Registry(
        (
            _registered(FITNESS, INSTRUCTIONS, "Be a coach."),
            _registered(SECURITY, INSTRUCTIONS, "Be careful."),
        )
    )

    written = registry.instructions()

    assert written.index("Fitness") < written.index("Security")
    assert "Be a coach." in written
    assert "Be careful." in written


def test_a_plugin_that_registered_nothing_to_say_adds_no_section() -> None:
    assert Registry((_registered(SECURITY, INSTRUCTIONS, "  "),)).instructions() == ""
