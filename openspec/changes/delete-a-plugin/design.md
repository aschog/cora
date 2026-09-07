## Context

The plugins folder is already live, so removing an entry unloads a plugin by the next
request. What is missing is a way to do it from the page, and the data left behind:
`.cora/documents/<field>`, that field's collection in the index, and every conversation
pinned to it. See proposal.md — Why.

## Goals / Non-Goals

- Goal: one call takes the entry and everything under it, in an order that can be retried.
- Goal: the name a request carries is resolved against what loaded, never against the
  filesystem.
- Goal: a symlink is unlinked, so a linked repository is never recursed into.
- Non-goal: unloading without deleting — moving an entry out of the folder already does
  that.
- Non-goal: new port methods; every half of this composes from methods the ports have.
- Non-goal: deleting a plugin named in `CORA_PLUGINS`, which returns at the next start.
- Non-goal: a field the configuration names, which holds documents and no plugin.

## Decisions

### Where the removal lives

- The seam is the listing: `Listed` already carries a plugin's source and the scope of
  every registration, so the cascade reads what to delete off what loaded.
- A new engine module takes the parts it needs — the folder, the listing, the knowledge
  base, the agent, the conversations — and removes one plugin over them.
- The engine module holds no paths of its own: the composition root hands it the folder,
  as it hands the output port its root today.
- `App` gains the removal alongside the agent and the stores, because the API is handed
  an `App` and nothing else.
- `LiveApp` needs no change: the folder signature moves when the entry goes, and the
  next request recomposes.

### The order, and what it costs

- Documents first, then conversations, then the entry — the listing is what names the
  fields, so deleting it first would make them unknowable.
- A half that fails leaves the plugin listed and deletable, which is the retry, rather
  than a half-deleted plugin nobody can name.
- Passages and files go through the same per-document delete the rail uses, over
  `sources` and `uploads`, so no store learns a new operation.
- What the filesystem raises leaves as cora's own refusal, because a page reading a
  bare 500 tells the reader cora could not be reached, which is false.
- Conversations are found by reading each session's pin, which is a checkpoint read per
  session and cheap at the scale one machine holds.

### The route, and what it refuses

- `DELETE /api/plugins/{name}` mirrors the three deletes the rails already have: no
  body, no content, and the listing read again after.
- The name is matched against the loaded listing, so a path, a traversal or an unknown
  name never reaches the filesystem — the rule `_field` applies to a scope.
- A plugin whose source is a module path is refused as fixed at start, which is the
  same sentence the README already tells operators.

### The page

- The control is the one the three rails already carry, with the confirmation the same
  component draws — the page learns no fourth way to delete something.
- The menu shows a control only for a field whose plugin is deleteable, which the
  plugin listing already says.
- Which fields go with a plugin is read off that listing too, rather than derived from
  what it registered: the rule is the engine's, and a question is not the place to
  read it a second way.
- One field draws the menu when something in it is deletable, though one field is
  nothing to pick between — otherwise the last plugin is deletable by hand alone.
- The question names the plugin, every field going with it, and what stays, because
  this is now the most destructive control on the page.
- After the delete the fields, the documents and the sessions are read again, as the
  existing removal hook does for a row.

## Risks / Trade-offs

- A real folder is deleted with no way back → the question names what goes, and a
  symlinked deployment loses only the link.
- A plugin registering a field another plugin also registers would lose that field's
  documents → the field goes only where the deleted plugin is the last to bring it.
- A turn in flight keeps the composition it started with and may search a field being
  emptied → it answers from fewer passages, which is the same race a deleted document
  already runs.
- Reading a pin per session is linear in sessions → acceptable on one machine, and the
  read is the one the page already makes per thread.
- A thread pinned to the field but never answered is listed nowhere, so it outlives the
  plugin → it is reached by nothing, which is where deleting a conversation already
  leaves one.
- A conversation whose pin is settled draws the name and no menu, so deleting is done
  from another conversation → the control belongs to the field, not to the turn.

## Open Questions

None.
