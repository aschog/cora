## Why

Vocabulary arrives as a screenshot of somebody else's app, and cora reads text, so what
is being learnt never reaches a field.

## What Changes

- A new plugin brings cora a `vocab` field: instructions and a page, and no tools
- The page reads a dropped screenshot in the reader's own browser and offers rows
- The reader corrects those rows before anything is saved — the reading is a draft
- Saving writes one Markdown document into the field: a heading and a two-column table
- The heading names the language, so several languages share one field as documents
- The image never leaves the browser, and only the finished Markdown reaches cora
- The one host the page fetches its reader from is named, as the trainer's are
- cora answers about a saved list from its own document search, citing it
- Capability `plugins` gains what the vocab field brings
- Not here: practising the words, which is the change after this one

## Impact

- `plugins/vocab/` — the new package: its registration, its page, its own suite
- `pyproject.toml` — a fifth workspace plugin, named where the other four are
- `tests/guards/test_packaging.py`, `tests/guards/test_architecture.py` — a fifth entry
- `frontends/react/ui/e2e/vocab.spec.ts` — the browser tier draws the page and saves
- `docs/what-ships-with-it.md` — the fifth plugin, and what its field is for
- `docs/privacy-and-ethics.md` — the host a reader's browser reaches for the reading
- Left alone: the core, which `register_page` and `/api/documents` already offer
- Left alone: the other four plugins and the fields they bring
