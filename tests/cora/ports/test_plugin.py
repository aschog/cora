from dataclasses import fields

import pytest

from cora.ports.plugin import Plugin, ToolResult


def test_ok_result_carries_payload_and_no_error() -> None:
    result = ToolResult(call_id="call-1", payload=3)

    assert result.payload == 3
    assert result.error is None


def test_error_result_carries_error_and_no_payload() -> None:
    result = ToolResult(call_id="call-1", error="unknown tool 'nope'")

    assert result.error == "unknown tool 'nope'"
    assert result.payload is None


def test_result_with_both_payload_and_error_is_rejected() -> None:
    with pytest.raises(ValueError):
        ToolResult(call_id="call-1", payload=3, error="boom")


def test_result_with_neither_payload_nor_error_is_rejected() -> None:
    with pytest.raises(ValueError):
        ToolResult(call_id="call-1")


def test_render_returns_the_error_message() -> None:
    assert ToolResult(call_id="c1", error="Unknown tool 'tdee'.").render() == (
        "Unknown tool 'tdee'."
    )


def test_render_returns_a_string_payload_as_is() -> None:
    assert ToolResult(call_id="c1", payload="2500 kcal").render() == "2500 kcal"


def test_render_serialises_other_payloads_as_json() -> None:
    result = ToolResult(call_id="c1", payload={"tdee": 2500, "unit": "kcal"})

    assert result.render() == '{"tdee": 2500, "unit": "kcal"}'


def test_a_plugin_needs_nothing_but_a_name() -> None:
    plugin = Plugin(name="bare")

    assert plugin.instructions == ""
    assert plugin.tools == ()
    assert plugin.validation_rules == ()


def test_a_plugin_carries_a_prompt_tools_and_rules_and_names_no_domain() -> None:
    """A plugin no longer declares a subject: nothing in the turn holds an answer
    against one, so there is nothing for the phrase to be part of."""
    assert [field.name for field in fields(Plugin)] == [
        "name",
        "instructions",
        "tools",
        "validation_rules",
    ]


def test_every_plugin_field_is_keyword_only() -> None:
    """Declaration order is not API: a fifth kind of contribution is a field with a
    default, and appending one may not break a plugin already written."""
    assert all(field.kw_only for field in fields(Plugin))
