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
"""


def extend(cora: Host) -> None:
    """A field that answers from the word lists it holds, and nothing else: searching
    them is cora's own tool, and reading a screenshot into one is cora's own screen."""
    cora.register_instructions(INSTRUCTIONS, scope=SCOPE)
