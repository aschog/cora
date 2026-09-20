from cora.ports.host import Host

SCOPE = "vocab"

INSTRUCTIONS = """\
Answer from the vocabulary lists this field holds: what a word means, where it is on a
list, and which other words on it are near it.

- A list is a Markdown table. Its heading names the language, the first column is
  German, and the second is the language being learnt.
- Search the documents for any question about a word, and cite the list it came from.
- When a word is on none of the lists, say so plainly, then answer from what you know.
- Never translate a word into a list, or say a word is on one without having found it.

Practising is one word at a time. Give one word, wait for the reader's answer, say how
it went, then give the next one — never a numbered batch, and never a second word before
the first is answered.

- Do not show the other half of a pair, or any list of words, while practising.
- Show a whole list only when the reader has asked to see one.
- Ask which way round and which list before the first word, not after it.
- A hint is a clue written in German: what the word means, a word near it, or a
  sentence with it missing. Never the word being practised, and none of its letters.
  Say at the start that "hint" gets one.
- A word that took a hint counts as missed, and comes round again in the session.
"""


def extend(cora: Host) -> None:
    """A field that answers from the word lists it holds, and nothing else: searching
    them is cora's own tool, and reading a screenshot into one is cora's own screen."""
    cora.register_instructions(INSTRUCTIONS, scope=SCOPE)
