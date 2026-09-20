## Why

A document is added from the rail, so a file the reader wants to ask about is added
somewhere other than where they are typing the question.

## What Changes

- The composer grows a control of its own for adding a file or a photo
- What it adds lands in the field the conversation is in, as the rail's control does
- It is the same upload: the same news, the same refusals, the same list changing
- The control says what it is doing while an upload is running, and stops taking another
- The rail keeps its own control, which stands over the list it changes
- Capability `frontend` gains what the composer can add
- Not here: reading a photo into text before it is kept, which is its own change

## Impact

- `frontends/react/ui/src/components/Answer.tsx` — the composer takes a file
- `frontends/react/ui/src/components/Answer.module.css` — the control beside the ask
- `frontends/react/ui/src/App.tsx` — the upload the rail holds, handed to the talk too
- `frontends/react/ui/e2e/documents.spec.ts` — a file added from the composer
- `docs/the-page.md` — where a document is added from
- Left alone: the upload itself, the field it lands in, and the news it makes
- Left alone: the rail's control, its list and every panel
