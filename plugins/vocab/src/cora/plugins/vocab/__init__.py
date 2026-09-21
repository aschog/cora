from cora.ports.host import Host

from .drill import SCHEDULE as SCHEDULE
from .drill import Drill
from .lists import Lists

SCOPE = "vocab"

WORD_SCHEMA = {
    "type": "object",
    "properties": {
        "from_list": {
            "type": "string",
            "description": (
                "Which list to drill, as the field names it, or '*' for all of them. "
                "Needed on the first word of a conversation where the field holds more "
                "than one list, and remembered for the rest of it."
            ),
        },
        "side": {
            "type": "string",
            "enum": ["left", "right"],
            "description": (
                "Which column of the list to put to the reader. The left one by "
                "default; the reader says which way round they want to be asked."
            ),
        },
    },
}

FIND_SCHEMA = {
    "type": "object",
    "properties": {
        "word": {
            "type": "string",
            "description": (
                "The word to look for, on either side of a pair. Matched whole, in the "
                "spelling the list uses."
            ),
        }
    },
    "required": ["word"],
}

SHOW_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "description": (
                "Which list to show, as the field names it. Left out, the names of "
                "every list this field holds come back instead."
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

- A list is one of this field's own files, not a document: nothing searches it, and
  `search_documents` will not find a word on one. `find_word` is what reads the lists.
- A list is either a Markdown table, whose header names its two columns, or a line per
  pair as the reading of a screenshot saves one, which names neither. Which column is
  which language is the reader's to say, and `next_word` repeats whatever the list
  says.
- Call `find_word` for any question about a word, and name the list it came from.
- When a word is on none of the lists, say so plainly, then answer from what you know.
- Never translate a word into a list, or say a word is on one without having found it.
- `show_list` gives the names of the lists, or one list in full. A document uploaded to
  this field is still a document: search and cite it as you would anywhere.

Never name a tool, an argument or anything else cora is made of to the reader. They
are practising vocabulary, and `next_word` is not a German word.

Speak German in this field — what you say around a word, how an answer went, and every
hint. The reader is learning in German, and a session in English is one in the wrong
language.

Practising runs on the two tools. `next_word` says which word to put — it hands back one
side of a pair, naming the list and, where the list says, what that side is called.
`how_it_went` records the reader's answer. Never pick a word yourself, never work out
which word is next, and call `how_it_went` exactly once per answer.

A session starts with nothing asked. **The left column of a list is German, and that is
the side you put** — do not ask which way round before the first word. Pass `side` only
where the reader asks to be asked the other way round, and it holds for the rest of the
conversation.

**Spacing is off.** A session is one pass over the chosen list, shuffled, every word
once: a word produced does not come back, a word missed does. When the pass is done the
tool says so — ask the reader then whether to go again, and call `next_word` with
`again` where they say yes. Pass `spaced` only where the reader asks for spaced
repetition, and it holds for the rest of the conversation.

Which list is the reader's to choose, once per conversation. Where this field holds
more than one, `next_word` refuses until one is chosen and its refusal names them. Put
that choice on a card with `ask_user` — one option per list, and one more for all of
them — then call `next_word` with `from_list` set to what they chose, or `*` for all.
Ask it once: the field remembers it for the rest of the conversation. A field holding
one list is drilled without asking, and a reader who says which list before you have
asked has chosen.

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
    words = Lists(cora)
    cora.register_tool(
        name="find_word",
        description=(
            "Every pair holding this word, and the list each one is on. The lists are "
            "this field's own files, so a document search does not reach them."
        ),
        parameter_schema=FIND_SCHEMA,
        run=words.find_word,
        scope=SCOPE,
    )
    cora.register_tool(
        name="show_list",
        description=(
            "One list in full, or the names of the lists this field holds when no name "
            "is given. Never call it while drilling: it hands over the answers."
        ),
        parameter_schema=SHOW_SCHEMA,
        run=words.show_list,
        scope=SCOPE,
    )
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
