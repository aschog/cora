## Context

The core now lets a field keep files that nothing indexes, and the correction dialog
already stands between a photo's reading and the field. What it does with the corrected
text is upload it, which makes a word list a searchable document. The vocab plugin reads
its pairs out of `cora.documents`, which is the same mistake seen from the other end.

## Goals / Non-Goals

**Goals:**

- A corrected reading can be kept as a named file of the field it was read in.
- A second photograph of the same list adds to it rather than making a second list.
- The vocab field drills from those files and stops needing its lists indexed.
- The shell learns nothing about vocabulary.

**Non-Goals:**

- Which column is German, and the drill defaults that follow from it; that is its own change.
- A list rail, a list editor, or anything that draws a list outside the dialog.
- Migrating the list already uploaded; it stays a document until re-read.
- Parsing on the page: the dialog moves text and never reads it as pairs.

## Decisions

- **The choice is offered in every field, not declared by a plugin** — every field keeps
  files, so the dialog exposes a capability rather than a plugin, and the shell keeps
  knowing nothing about vocab.
- **Merging is showing, not computing** — naming a list that exists puts its text in the
  box above the new reading, so the merge is the correction pass the reader was making
  anyway, and the route stays a plain replace.
- **De-duplication is the plugin's, at read time** — what counts as the same pair is
  vocabulary's question, and a file a person edits by hand will hold repeats no writer
  screened.
- **`pairs_in` keeps its two shapes** — a table and a line per pair, because the reading
  of a screenshot is lines and a list someone typed is a table.
- **The name box carries a `datalist`** — the browser's own completion over the names the
  field returned, which is a list element and no state.
- **The composer's ＋ opens a menu** — one item today, which is the point: it says what
  the control takes before it takes it.
- **The instructions drop the citation** — a file cannot be cited, so the field names the
  list in the sentence instead of numbering a passage.

## Risks / Trade-offs

- **A field that keeps no files still offers to write one**, which is the cost of not
  declaring; the alternative is a per-plugin switch in the shell.
- **A merged box can be large**, and the reader scrolls a textarea holding both lists; the
  cap refuses over a megabyte, which is far past a list anyone types.
- **Last writer wins** between the dialog and a hand edit, as the seam already says.
- **The list already uploaded stays a document**, so it is searched and not drilled until
  it is read again.

## What it touches

- **Ports:** none; the change rides the `Files` port the seam added.
- **Guards:** none new; the architecture and docs guards already cover what moves.
- **Diagrams:** none — no port, adapter or step is added.
- **Docs:** `docs/the-page.md` for what the dialog now offers.
