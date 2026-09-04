## Why

A fact cora has been told is one click from gone, while a conversation now asks first.

## What Changes

- Forgetting one fact asks first, over the page, as deleting a conversation does
- Forgetting everything asks the same way, naming what it would take
- Nothing is forgotten until the question is answered, and keeping it changes nothing
- A fact's row carries the same control a conversation's row does, named for the fact
- The word `forget` stops being a magenta word in the rail
- So the question a conversation raises becomes the question either rail raises
- New capability `memory`, which nothing before this change describes

## Impact

- `frontends/react/ui/src/components/MemoryPanel.tsx` — the row, and the control on it
- `frontends/react/ui/src/components/DeleteModal.tsx` — the question, told what to say
- `frontends/react/ui/src/App.tsx` — the two questions the memory rail raises
- `frontends/react/ui/src/styles.css` — the row's shape, and magenta's last destructive job
- Left alone: what cora remembers, when, and the endpoints that forget it
- Left alone: the sessions rail, which asks already and is not re-cut here
- Left alone: undoing a forget, which no store can offer
