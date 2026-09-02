import pytest

from cora.domain.errors import ConfigurationError
from cora.engine.plugin_set import RESERVED_TOOL_NAMES, Registry
from cora.engine.validation import CORA
from cora.ports.host import (
    BRIEFING,
    HANDLER,
    HAS_AN_EFFECT,
    INSTRUCTIONS,
    SCREENING,
    TOOL,
    Extension,
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
    """What the router chooses between and what the card says under a field's name. A
    line break is where the author's editor wrapped, so the paragraph is what is read,
    and a full stop is no boundary either — `e.g.` would cut the phrase it explains."""
    registry = Registry((_registered(FITNESS, INSTRUCTIONS, written, "fitness"),))

    assert registry.outline("fitness") == outlined


def test_a_scope_nobody_wrote_instructions_for_outlines_as_nothing() -> None:
    """The router is then given its name alone, which is all anyone said about it."""
    registry = Registry((_registered(FITNESS, INSTRUCTIONS, "Coaching.", "fitness"),))

    assert registry.outline("travel") == ""
    assert Registry().outline("fitness") == ""


def _extension(module: str, source: str = "") -> Extension:
    return Extension(module=module, extend=lambda cora: None, source=source)


def test_the_listing_names_what_each_plugin_registered_and_where() -> None:
    """One entry per plugin loaded, holding what a turn would take from it: a listing
    read off the registrations cannot drift from the app it describes."""
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
    """What a plugin may do is what the listing is for, and an effect is the loudest
    thing it can say. Carried as a note rather than a field of its own, so the two
    renderings and a fifth kind of contribution each read one shape."""
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


def test_a_plugin_that_registered_nothing_is_listed_with_nothing_under_it() -> None:
    """It is the one an operator most needs to see: loaded, and contributing none."""
    (quiet,) = Registry().listing((_extension(FITNESS),))

    assert quiet.contributions == ()
    assert quiet.of(TOOL) == quiet.of(HANDLER) == quiet.of(INSTRUCTIONS) == ()
    assert quiet.scopes == ()
