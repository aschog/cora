"""What a paused turn puts in front of the reader, and what comes back from it."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class FieldAsked:
    """One value on a card, and the schema the reader's control follows from.

    `schema` is JSON Schema, the same shape a tool declares its parameters in — so a
    card is built from what a tool already says about itself. `value` is what is known
    already, and `editable` says whether the reader may write it: an argument put up for
    approval is read, and a trip put up to be filled is written.

    `required` is carried on the field rather than left in the schema's own list,
    because a card's fields may come from more than one schema and only the field knows
    which of them required it.
    """

    name: str
    schema: dict[str, Any] = field(default_factory=dict)
    value: Any = None
    editable: bool = True
    required: bool = False


@dataclass(frozen=True)
class ActionOffered:
    """One way off a card, and what taking it says.

    `answer` is what travels back as the action taken, and `None` is the way out — a
    decline, or none of them. `needs_valid` holds the action closed until every
    required field on the card holds a value, which is what makes a half-filled form
    unsubmittable rather than submitted empty — an affordance of the page rather than a
    check, so what runs on the values is still whatever refuses a call it cannot make.

    `settled` is what the card says once this action has been taken, in the reader's
    own voice. Carried by the action because only whoever offered it knows what taking
    it meant — approving an effect and picking between two weights do not settle the
    same way. Left blank, the page says which action was taken and no more.
    """

    label: str
    answer: str | None = None
    note: str = ""
    needs_valid: bool = False
    settled: str = ""


@dataclass(frozen=True)
class Card:
    """What a stopped turn puts to the reader: a prompt, fields, and actions.

    Data alone, so a plugin adds a card without adding a component. What varies between
    a decision, a proposal and a form is which fields are writable and which actions
    are offered — not three shapes, and so not three renderers.
    """

    prompt: str
    fields: tuple[FieldAsked, ...] = ()
    actions: tuple[ActionOffered, ...] = ()

    @property
    def card(self) -> "Card":
        """Itself, so a card put straight to the reader is an `Asks` like the rest."""
        return self

    def __post_init__(self) -> None:
        """Refuse a card nobody can leave.

        The page has nothing else to offer while a card is open, so one the reader
        cannot get off is a conversation they cannot leave — and an action that waits
        for the required fields is no way out of a card they cannot fill.

        Raises:
            ValueError: The card offers no action, or none that can be taken as it
                stands.
        """
        if not self.actions:
            raise ValueError("a Card offers no action")
        if all(action.needs_valid for action in self.actions):
            raise ValueError("every action on a Card waits for it to be filled in")


@dataclass(frozen=True)
class Answer:
    """What the reader sent back: the action they took, and what they wrote.

    `action` is the taken action's own `answer`, and `None` is the way out. `values` is
    what the writable fields hold; a card of no fields settles on the action alone.
    """

    action: str | None = None
    values: Mapping[str, Any] = field(default_factory=dict)


@runtime_checkable
class Asks(Protocol):
    """Anything a turn can stop on.

    One port over all of them: what parks a run is the card, and what each shape is
    besides that is its own business.
    """

    @property
    def card(self) -> Card:
        """This, as the reader is shown it."""
        ...


def fields_of(
    schema: Mapping[str, Any], given: Mapping[str, Any] | None = None
) -> tuple[FieldAsked, ...]:
    """The fields of a JSON Schema object, carrying what is already known.

    The schema a tool declares is the one the card asks on, so the two cannot drift.
    Property order is the schema's, which is the order whoever wrote the tool chose.

    Args:
        given: Values already settled, filled into the fields they belong to.
    """
    known = given or {}
    required = schema.get("required", ())
    return tuple(
        FieldAsked(
            name=name,
            schema=dict(each) if isinstance(each, Mapping) else {},
            value=known.get(name),
            required=name in required,
        )
        for name, each in schema.get("properties", {}).items()
    )


def missing_from(
    schema: Mapping[str, Any], given: Mapping[str, Any]
) -> tuple[str, ...]:
    """The schema's required properties that `given` does not hold a value for."""
    return tuple(
        name for name in schema.get("required", ()) if given.get(name) in (None, "")
    )
