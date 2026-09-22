"""Reading the lists out loud: which list a word is on, and what one list holds.

A list used to be a document, so a word was found by searching the index and answered
with a citation. It is a file now, and nothing indexes a file — so what the search did
is done here, over the same pairs the drill reads, and the answer names the list
instead of numbering a passage.

Two tools rather than one that does both, and neither of them hands over a whole list
unasked: a drill running while the answers sit in the context is a drill the model can
read the answer off.
"""

from dataclasses import dataclass

from cora.ports.host import Host

from .words import Pair, pairs_of, sources_of

NO_LISTS = "This field holds no word lists yet."
NOWHERE = "'{word}' is on none of the lists this field holds."
NO_SUCH_LIST = "There is no list called '{name}'. This field holds: {held}."
MOST_SHOWN = 200


@dataclass(frozen=True)
class Lists:
    """The field's lists, as the two tools that read them."""

    cora: Host

    def find_word(self, word: str) -> str:
        """Every pair holding this word, and the list each one is on."""
        pairs = pairs_of(self.cora)
        if not pairs:
            return NO_LISTS
        wanted = word.strip().casefold()
        found = [pair for pair in pairs if wanted in _both(pair)]
        if not found:
            return NOWHERE.format(word=word.strip())
        return "\n".join(_said(pair) for pair in found)

    def show_list(self, name: str = "") -> str:
        """One list in full, or the names of the lists this field holds."""
        pairs = pairs_of(self.cora)
        if not pairs:
            return NO_LISTS
        held = sources_of(pairs)
        if not name.strip():
            return "\n".join(held)
        on_it = [pair for pair in pairs if pair.source == name.strip()]
        if not on_it:
            return NO_SUCH_LIST.format(name=name.strip(), held=", ".join(held))
        shown = on_it[:MOST_SHOWN]
        lines = [f"{pair.left} — {pair.right}" for pair in shown]
        if len(on_it) > MOST_SHOWN:
            lines.append(f"…and {len(on_it) - MOST_SHOWN} more.")
        return "\n".join(lines)


def _both(pair: Pair) -> tuple[str, str]:
    return (pair.left.casefold(), pair.right.casefold())


def _said(pair: Pair) -> str:
    return f"{pair.left} — {pair.right} (on {pair.source})"
