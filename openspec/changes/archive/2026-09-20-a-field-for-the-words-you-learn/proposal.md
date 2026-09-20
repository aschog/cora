## Why

Vocabulary has nowhere to live in cora: no field answers about the words somebody is
learning, so a list uploaded anywhere is answered from as prose.

## What Changes

- A new plugin brings cora a `vocab` field: instructions, and nothing else
- It answers from the word lists that field holds, citing the list a word is on
- It says a word is on no list rather than translating one onto one
- A list is a Markdown table, its heading naming the language and its columns the pair
- The field looks like every other field: no page, no tool, the conversation where it was
- Capability `plugins` gains what the vocab field brings
- Not here: reading a screenshot into a list, which is cora's own screen and its own change
- Not here: practising the words, which is the change after that

## Impact

- `plugins/vocab/` — the new package: its registration and its own suite
- `pyproject.toml` — a fifth workspace plugin, named where the other four are
- `tests/guards/test_packaging.py`, `tests/guards/test_architecture.py` — a fifth entry
- `docs/what-ships-with-it.md`, `docs/how-to/get-started.md`, `docs/tutorial/first-session.md` — the fifth plugin
- Left alone: the core, which already holds fields, documents and citations
- Left alone: the other four plugins and the fields they bring
