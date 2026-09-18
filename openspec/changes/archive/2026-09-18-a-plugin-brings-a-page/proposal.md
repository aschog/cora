## Why

A plugin may contribute to a turn but not to the screen, so a field that wants a
surface of its own has nowhere to put one.

## What Changes

- A plugin registers a directory of its own as the page of one field
- Cora serves that directory beside its own page, under a path naming the field
- The page is same-origin, so what it may call is cora's API as the reader holds it
- A page arrives and leaves with the plugin, as everything else a plugin brings does
- Two plugins claiming one field's page is refused at composition, naming both
- A page whose directory is gone costs that path a refusal, and nothing else
- The listing says that a plugin brings a page, and for which field
- The page asks cora which fields have a page, so a shell can find one
- Capability `plugins` gains a fourth kind of registration, and `frontend` the serving
- Capability `disclosure` says a plugin may now run script in the reader's browser
- Not here: where a shell draws it, which is the next change

## Impact

- `src/cora/ports/host.py` — `register_page`, a fourth kind, added surface only
- `src/cora/engine/host.py` — a page registered under a field, and never without one
- `src/cora/engine/plugin_set.py` — the kind listed, and one page per field enforced
- `src/cora/app/assembly.py` — the fields' pages on the app, as their names already are
- `frontends/react/src/cora/frontends/react/api.py` — the pages served and reported
- `frontends/react/ui/vite.config.ts` — the dev server proxies the new path too
- `docs/how-to/write-a-plugin.md`, `docs/the-page.md` — what a page is and what it costs
- `docs/privacy-and-ethics.md` — a page is script on cora's own origin, and says so
- Left alone: the turn, which a page takes no part in
- Left alone: the shell's layout, which the next change moves
- Left alone: deleting a plugin, which already takes the entry a page sits in
