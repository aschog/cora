# Submission notes

Answers to the questions a reviewer asks out loud, kept short. Not a spec and
not a design — the spoken version of what the code already says, kept here so it is
said the same way twice.

## Plugins

- **Why a plugin declares `CONTRACT`** — so a rename cora made, `register_tool` becoming
  `add_tool`, refuses an old plugin by name at startup instead of crashing it
  mid-conversation.
- **How deleting a plugin finds the documents to delete** — nothing is tagged by
  plugin, so `remove_plugin` in `src/cora/engine/removal.py` works out which fields
  leave with it. Its body is the whole answer, a step per line:

  1. `listed = _loaded(name, listing)` — the name is matched against the listing, and
     nothing of that name loaded is a refusal.
  2. `entry = _entry(listed, folder)` — the path comes from `listed.source`, never from
     the name, and `deletable` refuses one whose parent is not the plugins folder.
  3. `fields = fields_going(listed, listing, configured)` — this is the step that finds
     the documents:

     ```python
     retained = (
         {DEFAULT_SCOPE}
         | set(configured)
         | {
             scope
             for other in listing
             if other.name != listed.name
             for scope in other.scopes
         }
     )
     return tuple(scope for scope in listed.scopes if scope not in retained)
     ```

  4. `knowledge_base.forget(scope, source)` over `list_sources(scope)` for each field.
  5. `agent.forget(thread_id)` for each conversation pinned to one of them.
  6. `_delete(listed.name, entry)` last, so a delete that dies half way leaves the
     plugin still listed and still deletable.

  `listed.scopes` is `Listed.scopes` in `src/cora/ports/host.py`: the `scope=` the
  plugin passed to `register_tool`, `register_instructions` and `register_handler`.
  `KnowledgeBase` never learns a plugin's name at all.

## Documents

- **What `scope` and `name` are in `KnowledgeBase.forget(scope, name)`** — two different
  kinds of identifier, and the loop between them is the point:

  ```python
  for upload in self.retriever.uploads(scope, name):
      self.retriever.forget(scope, upload)
      self.documents.forget(scope, upload)
  ```

  1. `scope` is the field — which partition to delete from, so the same file ingested
     into a second field is left where it is.
  2. `name` is the uploaded filename, as `list_sources(scope)` lists it and the reader
     sees it. It is not what the stores delete by.
  3. `upload` is what they delete by, and the bytes name it: `add_file` computes
     `hashlib.sha256(data).hexdigest()`. Same bytes twice is one upload; same filename
     over different bytes is two uploads under one listed entry, and
     `retriever.uploads` is the mapping from the one to the many.
  4. All of them go, because the one entry is what the reader deleted — and a name
     nothing was uploaded under covers none, which is not an error.

  Inside the loop the passages leave the index before the file leaves the directory,
  which is `add_file`'s order run backwards: failing between the two leaves a file
  nothing can reach and the next upload of those bytes overwrites, where the other
  order would leave a document still listed whose citations open onto nothing.
