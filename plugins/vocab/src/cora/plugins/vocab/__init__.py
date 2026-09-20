from cora.ports.host import Host

from .drill import SCHEDULE as SCHEDULE
from .drill import Drill

SCOPE = "vocab"

WORD_SCHEMA = {
    "type": "object",
    "properties": {
        "side": {
            "type": "string",
            "enum": ["left", "right"],
            "description": (
                "Which column of the list to put to the reader. The left one by "
                "default; the reader says which way round they want to be asked."
            ),
        }
    },
}

WENT_SCHEMA = {
    "type": "object",
    "properties": {
        "word": {"type": "string", "description": "The word that was just put."},
        "right": {
            "type": "boolean",
            "description": "Whether the reader produced it. A hint counts as no.",
        },
    },
    "required": ["word", "right"],
}

INSTRUCTIONS = """\
Answer from the vocabulary lists this field holds: what a word means, where it is on a
list, and which other words on it are near it.

- A list is either a Markdown table, whose header names its two columns, or a line per
  pair as the reading of a screenshot saves one, which names neither. Which column is
  which language is the reader's to say, and `next_word` repeats whatever the list
  says.
- Search the documents for any question about a word, and cite the list it came from.
- When a word is on none of the lists, say so plainly, then answer from what you know.
- Never translate a word into a list, or say a word is on one without having found it.

Practising runs on the two tools. `next_word` says which word to put — it reads the
schedule this field keeps and hands back one side of a pair, naming the list and, where
the list says, what that side is called. Ask the reader which side they want to be
asked from before the first word, and pass it as `side`. `how_it_went` records
the reader's answer, and moves that word's schedule. Never pick a word yourself, never
work out when one is next due, and call `how_it_went` exactly once per answer.

Practising is one word at a time. Give one word, wait for the reader's answer, say how
it went, then give the next one — never a numbered batch, and never a second word before
the first is answered.

- Do not show the other half of a pair, or any list of words, while practising.
- Show a whole list only when the reader has asked to see one.
- Ask which way round before the first word, not after it, and pass it every time.
- A hint is a memory bridge, built the way Geisselhart's method builds one, and it is
  built for the word the reader has to produce — the answer, never the word already on
  the table, which they can see. Find a German word that sounds like that answer, tie
  the sound to what it means in one short picture — vivid, exaggerated, funny enough to
  stick — and ask which word the picture is pointing at.
- Write the hint in German, the keyword and the picture both, whichever language is
  being practised and whichever way round the drill is running. It is the language the
  reader has, and a clue in the language they are reaching for is a second puzzle.
- *chair*, asked from *der Stuhl*: **Schere**, and a chair made of giant scissors that
  snap shut as you sit down. "Welches englische Wort klingt wie *Schere*?"
- Where the answer is the German word, there is no sound to bridge to: give a clue
  about the word itself — a near-synonym, what it is for, or a sentence with a gap
  where it goes.
- A wrong guess gets a sharper picture or one more sound of the word, never the
  answer.
- `h` on its own asks for a hint, and is never an answer to the word on the table. Say
  so before the first word, and say it once.
- A word that took a hint counts as missed, and comes round again in the session.
"""


def extend(cora: Host) -> None:
    """A field that answers from the word lists it holds and drills from a schedule it
    keeps: searching the lists is cora's own tool, and reading a screenshot into one is
    cora's own screen."""
    cora.register_instructions(INSTRUCTIONS, scope=SCOPE)
    drill = Drill(cora)
    cora.register_tool(
        name="next_word",
        description=(
            "The word to put to the reader now, from the schedule this field keeps: "
            "what is due, then what has never been drilled. It hands back the side "
            "being asked and never the side the reader is to produce."
        ),
        parameter_schema=WORD_SCHEMA,
        run=drill.next_word,
        scope=SCOPE,
    )
    cora.register_tool(
        name="how_it_went",
        description=(
            "Say how the word just put went, and the schedule moves: missed comes "
            "back in this session, right waits a day, then six, then longer. Call it "
            "once per answer, for the word that was asked."
        ),
        parameter_schema=WENT_SCHEMA,
        run=drill.how_it_went,
        scope=SCOPE,
    )
