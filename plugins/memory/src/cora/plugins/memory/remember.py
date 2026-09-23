from dataclasses import dataclass

from cora.domain.errors import AdapterError
from cora.ports.memory import Memory
from cora.ports.plugin import ToolRefusal

REMEMBER_TOOL_NAME = "remember"
MAX_FACT_CHARS = 300
NOTHING_TO_REMEMBER = "There was nothing to remember."
TOO_LONG_TO_KEEP = "That note is too long to keep — the limit is {limit} characters."
REMEMBER_DESCRIPTION = (
    "Keep one fact about the user for later conversations, because they asked you to. "
    "Store what they asked you to store, in the third person — do not judge for "
    "yourself what is worth keeping, and never store what a document says."
)


@dataclass(frozen=True)
class RememberFact:
    """What `remember` runs: one fact into the store behind it.

    The two guards are the tool's own, not prompt validation: they stop a blank or
    oversized blob reaching the store. A store that cannot be written refuses rather
    than ending the turn — failing to file a note is not worth the user's answer.
    """

    memory: Memory

    def __call__(self, fact: str) -> str:
        """Keep the fact, and say so in the sentence the model reads.

        A fact already kept word for word is not kept twice, and says as much.

        Raises:
            ToolRefusal: The fact is blank, longer than `MAX_FACT_CHARS`, or the store
                could not be reached. The turn goes on either way.
        """
        if not fact.strip():
            raise ToolRefusal(NOTHING_TO_REMEMBER)
        if len(fact) > MAX_FACT_CHARS:
            raise ToolRefusal(TOO_LONG_TO_KEEP.format(limit=MAX_FACT_CHARS))
        try:
            if any(known.text == fact for known in self.memory.recall()):
                return f"Already remembered: {fact}"
            self.memory.remember(fact)
        except AdapterError as unreachable:
            raise ToolRefusal(unreachable.user_message) from unreachable
        return f"Remembered: {fact}"
