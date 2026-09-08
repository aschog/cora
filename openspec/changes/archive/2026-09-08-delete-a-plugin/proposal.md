## Why

A plugin you are finished with can only be removed from a shell, and its documents,
passages and conversations stay behind.

## What Changes

- Every field a dropped plugin brings carries a delete control, in the menu that lists
  the fields
- Confirming it deletes that plugin's entry in the plugins folder, a symlink and a
  package folder alike
- The documents of every field it registered go, and their passages with them
- Every conversation pinned to one of those fields goes, both halves of it
- What cora remembers about the user is left, and so is what an approved effect wrote
- A field no dropped plugin brings carries no control, having nothing to delete
- The question asked first names the plugin, the fields going with it, and what is not
  lost
- Capability `plugins` gains deleting a plugin and everything under it

## Impact

- `src/cora/engine/removal.py` — new, one plugin and its data removed over the parts
  it is given
- `src/cora/app/assembly.py` — the app carries where its plugins folder is, and what
  removing from it takes
- `frontends/react/src/cora/frontends/react/api.py` — a route deleting one loaded
  plugin by name
- `frontends/react/ui/src/components/ScopePicker.tsx` — a delete control per field it
  can delete
- `frontends/react/ui/src/App.tsx` — the question it asks, and the listings read again
  after
- `README.md` — the folder is live in both directions, and the page is one of them
- Left alone: the ports, whose existing methods compose into every half of this
- Left alone: memory and `cora-output`, which belong to the user rather than to a field
- Left alone: what `CORA_PLUGINS` names, fixed at start and holding nothing to delete
