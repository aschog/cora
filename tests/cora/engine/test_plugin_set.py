import pytest

from cora.domain.errors import ConfigurationError, InputRejectedError
from cora.engine.plugin_set import CORA_RULES, RESERVED_TOOL_NAMES, Registry
from cora.ports.host import INSTRUCTIONS, RULE, TOOL, Registration
from fixture_plugins import make_tool

FITNESS = "cora.plugins.fitness"
SECURITY = "cora.plugins.security"


def _registered(module: str, kind: str, value: object) -> Registration:
    return Registration(module=module, kind=kind, value=value)


class _Refuses:
    def __init__(self, message: str) -> None:
        self.message = message

    def apply(self, user_input: str) -> None:
        raise InputRejectedError(self.message)


def test_an_empty_registry_offers_no_tools_and_only_coras_rules() -> None:
    empty = Registry()

    assert empty.tools == ()
    assert empty.rules == CORA_RULES
    assert empty.modules == ()


def test_the_registered_tools_are_offered_in_registration_order() -> None:
    registry = Registry(
        (
            _registered(FITNESS, TOOL, make_tool("bmi")),
            _registered(SECURITY, TOOL, make_tool("tdee")),
            _registered(SECURITY, TOOL, make_tool("macros")),
        )
    )

    assert [tool.name for tool in registry.tools] == ["bmi", "tdee", "macros"]


def test_coras_rules_run_ahead_of_every_registered_one_in_order() -> None:
    guard, domain = _Refuses("first"), _Refuses("second")

    registry = Registry(
        (_registered(SECURITY, RULE, guard), _registered(FITNESS, RULE, domain))
    )

    assert registry.rules == (*CORA_RULES, guard, domain)


def test_a_module_that_registered_anything_is_named_once() -> None:
    """What the log line says was loaded: the modules, in the order they first
    registered, however many things each of them registered."""
    registry = Registry(
        (
            _registered(FITNESS, TOOL, make_tool("bmi")),
            _registered(FITNESS, RULE, _Refuses("no")),
            _registered(SECURITY, RULE, _Refuses("no")),
        )
    )

    assert registry.modules == (FITNESS, SECURITY)


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

    written = registry.instructions

    assert written.index("Fitness") < written.index("Security")
    assert "Be a coach." in written
    assert "Be careful." in written


def test_a_plugin_that_registered_nothing_to_say_adds_no_section() -> None:
    assert Registry((_registered(SECURITY, INSTRUCTIONS, "  "),)).instructions == ""
