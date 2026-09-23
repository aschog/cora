import pathlib

import pytest

from cora.domain.errors import ConfigurationError
from cora.engine.field_tools import BASH_TOOL_NAME, READ_TOOL_NAME, WRITE_TOOL_NAME
from cora.engine.plugin_set import RESERVED_TOOL_NAMES, Registry
from cora.engine.validation import CORA
from cora.ports.host import (
    FILES,
    HANDLER,
    HAS_AN_EFFECT,
    INSTRUCTIONS,
    PAGE,
    SCREENING,
    TOOL,
    Extension,
    Registration,
    Subscription,
)
from cora.ports.plugin import Tool
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


def test_the_registered_tools_are_offered_in_registration_order() -> None:
    registry = Registry(
        (
            _registered(FITNESS, TOOL, make_tool("bmi")),
            _registered(SECURITY, TOOL, make_tool("tdee")),
            _registered(SECURITY, TOOL, make_tool("macros")),
        )
    )

    assert [tool.name for tool in registry.tools()] == ["bmi", "tdee", "macros"]


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


WRAPPED = """\
Answer travel questions — destinations, routes, timing and logistics — from the
user's own documents.

- Search the documents for anything about a place, and cite what you used.
"""


@pytest.mark.parametrize(
    ("written", "outlined"),
    [
        (
            WRAPPED,
            "Answer travel questions — destinations, routes, timing and logistics "
            "— from the user's own documents.",
        ),
        ("One line, and no more of it.", "One line, and no more of it."),
        (
            "Answer questions about e.g. trains. Cite them.",
            "Answer questions about e.g. trains. Cite them.",
        ),
        ("", ""),
    ],
)
def test_a_scopes_outline_is_the_paragraph_its_instructions_open_with(
    written: str, outlined: str
) -> None:
    registry = Registry((_registered(FITNESS, INSTRUCTIONS, written, "fitness"),))

    assert registry.outline("fitness") == outlined


def _extension(module: str, source: str = "") -> Extension:
    return Extension(module=module, extend=lambda cora: None, source=source)


def test_the_listing_names_what_each_plugin_registered_and_where() -> None:
    registry = Registry(
        (
            _registered(
                CORA, HANDLER, Subscription(SCREENING, refuses_containing("x"))
            ),
            _registered(FITNESS, INSTRUCTIONS, "Coach.", "fitness"),
            _registered(FITNESS, TOOL, make_tool("bmr"), "fitness"),
            _subscribed(FITNESS, SCREENING),
            _registered(SECURITY, TOOL, make_tool("scan"), "travel"),
        )
    )

    listed = registry.listing((_extension(FITNESS), _extension(SECURITY, "notes.py")))

    coaching, guarding = listed
    assert (coaching.name, coaching.source) == ("fitness", FITNESS)
    assert (guarding.name, guarding.source) == ("security", "notes.py")
    assert [each.name for each in coaching.of(TOOL)] == ["bmr"]
    assert [each.name for each in coaching.of(HANDLER)] == [SCREENING]
    assert coaching.of(INSTRUCTIONS)
    assert coaching.scopes == ("fitness",)
    assert [each.system_wide for each in coaching.contributions] == [False, False, True]


def test_a_tool_that_changes_something_outside_cora_is_listed_as_doing_so() -> None:
    registry = Registry(
        (
            _registered(FITNESS, TOOL, make_tool("bmr"), "fitness"),
            _registered(FITNESS, TOOL, make_tool("book_it", effect=True), "fitness"),
        )
    )

    (listed,) = registry.listing((_extension(FITNESS),))

    assert [(each.name, each.note) for each in listed.of(TOOL)] == [
        ("bmr", ""),
        ("book_it", HAS_AN_EFFECT),
    ]


def test_two_plugins_bringing_one_fields_page_are_refused_by_name() -> None:
    with pytest.raises(ConfigurationError) as refused:
        Registry(
            (
                _registered(FITNESS, PAGE, pathlib.Path("/a"), "fitness"),
                _registered(SECURITY, PAGE, pathlib.Path("/b"), "fitness"),
            )
        )

    assert FITNESS in str(refused.value)
    assert SECURITY in str(refused.value)
    assert "fitness" in str(refused.value)


def test_two_plugins_bringing_a_page_each_for_their_own_field_compose() -> None:
    registry = Registry(
        (
            _registered(FITNESS, PAGE, pathlib.Path("/a"), "fitness"),
            _registered(SECURITY, PAGE, pathlib.Path("/b"), "travel"),
        )
    )

    assert registry.pages() == {
        "fitness": pathlib.Path("/a"),
        "travel": pathlib.Path("/b"),
    }


def test_a_page_is_listed_under_its_field_and_names_no_directory() -> None:
    registry = Registry((_registered(FITNESS, PAGE, pathlib.Path("/a"), "fitness"),))

    [coaching] = registry.listing((_extension(FITNESS),))

    [page] = coaching.of(PAGE)
    assert (page.name, page.scope, page.note) == ("", "fitness", "")


def test_the_names_cora_keeps_are_its_three_tools_and_no_other() -> None:
    assert set(RESERVED_TOOL_NAMES) == {READ_TOOL_NAME, WRITE_TOOL_NAME, BASH_TOOL_NAME}
    assert not {"remember", "ask_user", "ask_user_for", "search_documents"} & set(
        RESERVED_TOOL_NAMES
    )


def _claiming(scope: str) -> Registry:
    return Registry(
        (Registration(module="vocab", kind=FILES, value=None, scope=scope),)
    )


def _own() -> tuple[Tool, ...]:
    return (
        make_tool(READ_TOOL_NAME),
        make_tool(WRITE_TOOL_NAME),
        make_tool(BASH_TOOL_NAME),
    )


def test_a_field_whose_files_are_its_plugins_is_offered_none_of_coras_three() -> None:
    offered = _claiming("vocab").offering(_own(), frozenset({"vocab"}))

    assert [tool.name for tool in offered] == []


def test_every_other_field_is_offered_all_three() -> None:
    registry = _claiming("vocab")

    offered = registry.offering(_own(), frozenset({"travel"}))

    assert [tool.name for tool in offered] == [
        READ_TOOL_NAME,
        WRITE_TOOL_NAME,
        BASH_TOOL_NAME,
    ]


def test_a_turn_reaching_a_claimed_field_at_all_is_offered_none_of_them() -> None:
    # Read and write refuse a turn running in two fields anyway, and a command has to
    # pick one directory: the claim is the safer answer wherever it is in reach.
    offered = _claiming("vocab").offering(_own(), frozenset({"vocab", "travel"}))

    assert offered == ()


def test_what_the_plugins_registered_still_follows_coras_own() -> None:
    registry = Registry(
        (
            Registration(
                module="travel", kind=TOOL, value=make_tool("price"), scope=None
            ),
            Registration(module="vocab", kind=FILES, value=None, scope="vocab"),
        )
    )

    offered = registry.offering(_own(), frozenset({"travel"}))

    assert [tool.name for tool in offered][-1] == "price"
