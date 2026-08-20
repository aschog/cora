import pytest

from cora.domain.errors import ConfigurationError, InputRejectedError
from cora.engine.plugin_set import CORA_RULES, RESERVED_TOOL_NAMES, PluginSet
from fixture_plugins import make_plugin, make_tool

FITNESS = "cora.plugins.fitness"
SECURITY = "cora.plugins.security"


def test_a_composed_set_names_no_domain() -> None:
    coach = make_plugin(name="Coach", tools=())
    guard = make_plugin(name="Guard", tools=())

    composed = PluginSet(((FITNESS, coach), (SECURITY, guard)))

    assert not hasattr(composed, "scope")


class _Refuses:
    def __init__(self, message: str) -> None:
        self.message = message

    def apply(self, user_input: str) -> None:
        raise InputRejectedError(self.message)


def test_an_empty_set_offers_no_tools_and_only_coras_rules() -> None:
    empty = PluginSet()

    assert empty.tools == ()
    assert empty.rules == CORA_RULES


def test_the_offered_tools_run_in_config_order() -> None:
    first = make_plugin(tools=(make_tool("bmi"),))
    second = make_plugin(tools=(make_tool("tdee"), make_tool("macros")))

    composed = PluginSet(((FITNESS, first), (SECURITY, second)))

    assert [tool.name for tool in composed.tools] == ["bmi", "tdee", "macros"]


def test_coras_rules_run_ahead_of_every_plugins_in_config_order() -> None:
    guard, domain = _Refuses("first"), _Refuses("second")
    first = make_plugin(tools=(), validation_rules=(guard,))
    second = make_plugin(tools=(), validation_rules=(domain,))

    composed = PluginSet(((SECURITY, first), (FITNESS, second)))

    assert composed.rules == (*CORA_RULES, guard, domain)


def test_two_plugins_offering_one_tool_name_is_a_config_error() -> None:
    clash = make_tool("bmi")

    with pytest.raises(ConfigurationError) as excinfo:
        PluginSet(
            (
                (FITNESS, make_plugin(tools=(clash,))),
                (SECURITY, make_plugin(tools=(clash,))),
            )
        )

    message = excinfo.value.user_message
    assert FITNESS in message
    assert SECURITY in message
    assert "bmi" in message


@pytest.mark.parametrize("reserved", sorted(RESERVED_TOOL_NAMES))
def test_a_plugin_taking_a_name_of_coras_own_is_a_config_error(reserved: str) -> None:
    with pytest.raises(ConfigurationError) as excinfo:
        PluginSet(((FITNESS, make_plugin(tools=(make_tool(reserved),))),))

    assert FITNESS in excinfo.value.user_message
    assert reserved in excinfo.value.user_message


def test_one_module_listed_twice_is_a_config_error() -> None:
    """Otherwise the tool-name collision reads as a plugin colliding with itself, and
    the user is told nothing about what they actually typed."""
    with pytest.raises(ConfigurationError) as excinfo:
        PluginSet(((FITNESS, make_plugin()), (FITNESS, make_plugin())))

    assert FITNESS in excinfo.value.user_message
    assert "twice" in excinfo.value.user_message


def test_two_plugins_are_two_sections_under_their_names_in_config_order() -> None:
    coach = make_plugin(name="Fitness coaching", instructions="Be a coach.", tools=())
    guard = make_plugin(name="Safety", instructions="Be careful.", tools=())

    composed = PluginSet(((FITNESS, coach), (SECURITY, guard))).instructions

    assert composed.index("Fitness coaching") < composed.index("Safety")
    assert "Be a coach." in composed
    assert "Be careful." in composed


def test_a_plugin_with_nothing_to_say_adds_no_section() -> None:
    silent = make_plugin(name="Silent", instructions="", tools=())

    assert PluginSet(((SECURITY, silent),)).instructions == ""
