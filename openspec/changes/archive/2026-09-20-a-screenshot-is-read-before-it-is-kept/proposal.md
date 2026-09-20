## Why

cora reads text, so a screenshot of what somebody wants to ask about is refused at the
door — and the words in it are the only part that was ever wanted.

## What Changes

- A photo added beside the question is read into text in the reader's own browser
- The image is never uploaded: what leaves the browser is the text, and only when saved
- What was read is put up to correct first, because a reading is a draft
- Saving keeps it as a Markdown document of the field, named after the image
- Discarding keeps nothing, and the field is as it was
- A reading that found no text says so, and a reader that could not be fetched says that
- The one host the reading is fetched from is named, as the trainer's are
- Any field gets it: the words in a photo are documents like any other
- Capability `frontend` gains what happens to a photo before it is kept

## Impact

- `frontends/react/ui/src/reading.ts` — the reader, fetched once and run in the browser
- `frontends/react/ui/src/components/ReadImage.tsx` — what was read, put up to correct
- `frontends/react/ui/src/App.tsx` — a photo goes to the reading, a file to the upload
- `frontends/react/ui/e2e/documents.spec.ts` — a photo read, corrected and kept
- `docs/the-page.md`, `docs/privacy-and-ethics.md` — the reading, and where it comes from
- Left alone: the upload, the field it lands in, and the news it makes
- Left alone: cora's own side, which never sees an image
