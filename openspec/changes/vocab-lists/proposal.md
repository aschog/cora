## Why

A vocabulary list is drill data, but the only way to save one makes it a searchable document.

## What Changes

- A photo read on the page can be kept as one of the field's own files instead of a document
- The reader names it, and the names the field already holds are offered as they type
- Choosing a name that exists opens that file in the box, so the correction pass covers the merge
- The composer's ＋ opens a menu naming what it takes, rather than the file picker itself
- The vocab field reads its lists from the field's files rather than from its documents
- A pair that appears twice on one list is drilled once
- Capability `frontend` — what a photo read on the page may be kept as
- Capability `plugins` — where the vocab field's lists live, and how a word is answered from one

## Impact

- `frontends/react/ui/src/components/ReadImage.tsx`, `.module.css` — the name box, the choice, the merge
- `frontends/react/ui/src/components/Answer.tsx`, `.module.css` — the ＋ opens a menu
- `frontends/react/ui/src/App.tsx` — the reading is kept as a file or uploaded, and the field's names are read
- `frontends/react/ui/src/cora.ts` — the four file routes, as the page calls them
- `plugins/vocab/src/cora/plugins/vocab/drill.py`, `words.py` — lists read from the field's files, pairs deduplicated
- `plugins/vocab/src/cora/plugins/vocab/__init__.py` — the instructions say where a list lives and drop the citation
- `openspec/specs/plugins` — the vocab field's lists are its files, not its documents
- Left alone: the schedule, SM2, the two tools, ordinary documents in the vocab field, every other plugin
