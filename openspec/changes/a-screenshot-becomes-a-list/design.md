## Context

cora reads `.txt`, `.md` and `.pdf`, its model port carries text, and a plugin owns no
route of its own — so a screenshot has nowhere to enter. See proposal.md — Why.

## Goals / Non-Goals

**Goals** — a vocabulary list entering cora as a document the reader corrected first,
with the image never leaving the machine it was taken on.

**Non-Goals** — practising the words, which is the next change. Reading images anywhere
else in cora. A store of the plugin's own.

## Decisions

**The reading happens in the page, because the image cannot reach the plugin.**

- A tool is called with JSON the model wrote, so no image reaches one.
- An image loader in the core would index the reading before anybody corrected it, and
  a core change has to serve every plugin rather than this one.
- The page is the seam that already exists: `register_page` draws it, `/api/documents`
  takes what it produces, exactly as the trainer saves a workout.

**The reading runs in the browser, from one named host.**

- `tesseract.js` is Tesseract compiled to WebAssembly, so the recognition runs on the
  reader's machine and the image is never uploaded.
- Its script, its WebAssembly core and its language data are pinned on
  `cdn.jsdelivr.net`, so the page reaches one host and the suite names one host.
- They are fetched once and the browser keeps them, so a second list costs no download.
- Rejected: shipping the language data in the plugin — megabytes of binary in the tree
  for a file the browser would cache anyway.

**The reader picks the language, and the document says which it is.**

- The heading carries the language, so one field holds many languages as documents and
  nothing has to be configured before a list is imported.
- The page offers the languages it has recognition data for, which is what the reader
  may pick from.
- Rejected: a setting per deployment — the reader changes language between sessions,
  and a setting is a restart.

**A list is a Markdown table, German in the first column.**

- A pipe table is unambiguous where a word holds a hyphen or a comma, which a dash
  separator is not.
- It is Markdown, so it chunks, embeds, renders in the rail and cites like every other
  document, with no reader of its own.
- The direction is fixed in the file and chosen at practice time, so the document says
  what the pair is rather than what to ask.

**The page reads its field out of the path it is served under.**

- It is served at its field's address, so it uploads into that field without the plugin
  writing its own name into a file the plugin also names.

**The plugin registers instructions and a page, and no tool.**

- Searching the field is `search_documents`, which every field already has.
- A tool that listed the lists would be a second way to read what the rail shows.

## Risks / Trade-offs

- Recognition of a phone screenshot is imperfect → the correction step is not a courtesy,
  it is where the document is actually written.
- The first reading downloads a few megabytes → cached afterwards, and a fetch that
  fails says so rather than reading as an empty screenshot.
- The language data is a third party's → named in the plugin's own suite and on the
  privacy page, as the trainer's four hosts are.
- The page is one file of JavaScript that only the browser tier exercises → its parsing
  and its table writing are called in the page rather than lifted out of it.
- Two imports of one name are two documents → the store already keeps them apart, and
  the rail lists the name once.

## Ports, guards and diagrams

- No port and no core change: `register_page` and `/api/documents` are what this uses.
- The packaging and architecture guards gain a fifth plugin and its empty import set.
- No diagram changes: nothing about the composition moves.
