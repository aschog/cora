## Context

The composer takes a file and hands it to the upload. cora reads `.txt`, `.md` and
`.pdf`, so a photo is refused. See proposal.md — Why.

## Goals / Non-Goals

**Goals** — the words in a photo, corrected by the reader, kept as a document of the
field they were added in.

**Non-Goals** — reading images on cora's side, a language the reader picks, the shape of
what was read, and anything a particular field wants it to mean.

## Decisions

**The reading runs in the browser.**

- Tesseract compiled to WebAssembly recognises the text on the reader's own machine, so
  the image is never uploaded and cora stays a thing that reads text.
- Rejected: an image loader in the core — it would index a reading nobody corrected, and
  it would put an OCR engine and its trained data in every deployment.

**It is fetched, not bundled.**

- The script, its WebAssembly core and its trained data are pinned on
  `cdn.jsdelivr.net` and loaded the first time a photo is added, then cached.
- The page carries no new dependency, nothing is downloaded by a reader who never adds a
  photo, and the browser tier can stand a reader in for the real one.
- Rejected: an npm dependency — it bundles the script but still fetches the trained
  data, and it puts a reader in every build for a feature not every deployment uses.

**What was read is a draft in front of the reader.**

- Recognition of a photograph is imperfect, so the text is put up to correct before it
  is anything cora holds — the same shape as a confirmation, and it keeps nothing.
- Saving goes through the upload the composer already makes, so there is one path into
  a field.

**Two silences, two sentences.**

- A photo with no text in it and a reading that never ran are different facts, and
  reporting either as the other sends the reader to fix the wrong thing.

**German and English are what it is read with.**

- The reader writes in one or the other, and trained data is fetched per language.
- A picker is a story of its own, and the text is corrected by hand anyway.

## Risks / Trade-offs

- A first reading downloads a few megabytes → cached afterwards, and a failure to fetch
  says so rather than reading as an empty photo.
- The trained data is a third party's → named in the privacy page, as the trainer's
  hosts are.
- Recognition is imperfect → the correction step is where the document is written.

## Ports, guards and diagrams

- No port and no core change: the API this uses is the upload the composer uses.
- No guard changes and no diagram changes: nothing about the composition moves.
