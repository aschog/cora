# Cited sources

The Sources panel lists every retrieved-and-deduped file, not the ones the answer
actually cited — so a one-source answer shows three. Worse, the two `[n]` schemes
disagree: `build_context_block` numbers **chunks**, while the panel re-numbers the
**deduped source list**, so citation `[n]` and panel `[n]` only coincide by accident.

Fix both at once by making the citation number *be* the source number.

## Acceptance criteria

- Context numbers by **unique source** (first-seen order); every chunk of one file
  carries that file's number, so the model cites a source, not a chunk.
- The panel lists **only** the sources the answer cites, each under the **same**
  number the answer used. `[1]` in the answer == `[1]` in the panel; gaps are kept
  (cite `[1]` and `[3]` → panel shows `[1]` and `[3]`, never renumbered to `[1] [2]`).
- Uncited answer → empty panel. A citation out of range or a repeat → ignored / once.

## Design

The number→source mapping has **one owner**. `build_context` returns the prompt block
*and* the numbered table it used; the engine resolves citations against that table and
never recomputes numbering. A custom builder that renumbers supplies its own table, so
the prompt and the citations cannot drift — the seam stays honest.

- **`Source(number, name)`** — a frozen dataclass in `chat_engine`; `ChatResult.sources`
  becomes `tuple[Source, ...]` (was `tuple[str, ...]`).
- **`Context(text, sources)`** — what `build_context` now returns: the block plus its
  ordered sources, where `sources[i]` is number `i+1`. (`build_context` signature goes
  `list[RetrievedChunk] -> Context`, was `-> str`.)
- **`build_context_block`** — number by unique source (first-seen order); prefix each
  chunk line with its source's number; citation rule says *source*; return the `Context`.
- **`cited_numbers(text)`** — pure helper: distinct `[n]` in order of first appearance.
- **`ChatEngine.answer`** — build the context once; after the tool loop, resolve
  `cited_numbers(answer)` against `context.sources` and return the cited-only `Source`s.
- **`numbered_sources`** — render `[s.number] s.name`; stop re-enumerating.

## TDD checklist

- [x] `cited_numbers("...[1]...[3]...[1]")` → `(1, 3)` — distinct, appearance order;
      no brackets → `()`.
- [x] `build_context_block`: two chunks of one source share its number; a second
      source gets the next number; rule mentions "source"; returns a `Context` whose
      `sources` is the ordered unique-source table.
- [x] `answer` citing `[2]` returns `(Source(2, "b.txt"),)` — not the uncited `a.txt`.
- [x] `answer` citing nothing returns `()`.
- [x] `answer` with an out-of-range `[9]` ignores it.
- [x] `numbered_sources((Source(1,"a"), Source(3,"b")))` → `["[1] a", "[3] b"]`;
      `()` → `[]`.
  > These four landed as one green step: flipping `ChatResult.sources` to
  > `tuple[Source, ...]` ripples engine→formatter atomically, so splitting them
  > would leave the tree red.
- [x] UI: upload a doc, ask, model cites `[1]` → panel shows exactly that one source
      (retrieved-but-uncited seed docs stay out — the regression guard for the bug).

## Review findings (Phase 3)

- [x] Guard incidental brackets: `cited_numbers` ignores `[n]` glued to a word or
      `]` (`list[2]`, `arr[0][1]`), so only real citations count. Partial by nature —
      a spaced `step [2]` still matches; that's an accepted limit of a bracket scheme.
- [x] Honest seam: `Context.sources` carries `Source` objects, so a custom
      `build_context` owns its numbering and `_cited_sources` resolves by number,
      not by position.
- [x] Panel lists cited sources in ascending source-number order, not citation order.
- [x] `build_context_block` numbers non-adjacent repeats of a source the same.

## Fallout to update

`test_chat_engine.py` (unique-sources test now means cited-only; injected-`build_context`
test returns a `Context`, and `test_system_message…`/`build_context_block` assert on
`.text`), `test_formatting.py` (Source inputs), `test_chat.py` / `test_thread.py`
(sources carry numbers).
