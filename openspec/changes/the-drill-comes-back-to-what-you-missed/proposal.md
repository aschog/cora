## Why

The drill forgets: what was missed today is gone when the conversation is, so every
session starts from the whole list rather than from the words that are actually hard.

## What Changes

- The vocab field gets a schedule of its own, kept for good in the plugin's own store
- Asking for a word hands back the one that is due, and the prompt side of it alone
- What was missed comes back in the same session, and again sooner than what was known
- Spacing is SM-2: an interval and an ease per word, a day, six days, then ease-wide
- A word never drilled is new, and new words fill a session the due ones have not
- Saying how it went is one call, so the schedule moves only on the reader's answer
- The field's instructions drill through those tools rather than from what it can see
- Capability `plugins` gains what the vocab field keeps and how it picks a word

## Impact

- `plugins/vocab/src/cora/plugins/vocab/sm2.py` — the spacing, as arithmetic on one word
- `plugins/vocab/src/cora/plugins/vocab/schedule.py` — the schedule as text, and what is due
- `plugins/vocab/src/cora/plugins/vocab/words.py` — the pairs, read out of the field's lists
- `plugins/vocab/src/cora/plugins/vocab/__init__.py` — two tools, and instructions that use them
- `docs/what-ships-with-it.md` — what the field does now
- Left alone: the core, which `a-plugin-keeps-what-it-learned` finished
- Left alone: the lists themselves, which stay documents the reader owns
