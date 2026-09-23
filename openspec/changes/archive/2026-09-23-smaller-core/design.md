## Context

- Cora's own input screen already rides the registry as an extension, so the seam exists.
- The host hands a plugin search, memory, model, store, state and files; only writing into the index is missing.
- Every gathering tool already puts a card through the gate, which is the hook the ask tools can ride.
- The frontends reach documents through the app's knowledge base, and every upload through one route.
- Two guards frame the move: the core names no plugin, and a plugin imports no engine or adapter.
- See proposal.md for why.

## Goals / Non-Goals

**Goals:**

- The engine knows no subject: no ask, no remember, no search, no ingestion, no loader.
- Three tools of cora's own, all over one directory: the field's.
- One primitive for what lands in a field, whoever puts it there.
- Every frontend route keeps its path and its refusals, and the page draws cards as before.

**Non-Goals:**

- Moving the gate, citations or any store.
- A sandbox: the field's directory bounds paths, not what a command can reach.
- Indexing files already in a field when the plugin arrives later.
- A plugin serving API routes of its own.

## Decisions

- **Shipped plugins, not built-in extensions.** A member under `plugins/` is what the north star calls a behaviour, and the no-plugin-names guard then holds for ask, memory and documents too.
- **Three tools over the field's directory.** Read and write go through the field files the host already binds; the command goes through a new `Shell` port whose adapter runs a subprocess with the field's directory as its working directory. Names are checked by the plain-name rule; a command is refused when it plainly names a parent, an absolute path or one of the machine's own places. That is an argument check over the command's text, not a sandbox: a path a variable or a substitution builds gets through, and the command reaches the network regardless. The tool's description says so to the model rather than promising containment it does not have. The user decided none of the three waits for approval, so none declares an effect.
- **Read and the command are untrusted.** A file is the user's own the way a passage is, and a command prints whatever it finds; both reach the model behind the label.
- **Output is capped, time is bounded.** Two settings of the deployment; the cut and the stop are told to the model in the result.
- **The ask tools ride the gate.** Both register with a card hook, so the gate puts the card and the tool runs on the answer. The ask step, its route and the loop's ask slot leave the engine; the rounds go model, gate, tools. An ask costs the round it was made in.
- **A card names where the action lands.** One optional field on the card: the argument the reader's action is written into. The core's own decision card leaves it blank, so the focus step's fork is unchanged; the ask plugin's fork names it, and its way out is an action too, so the tool runs and words the decline itself. Rejected: a one-field enum card, which the two-values rule refuses.
- **A fork is put once per conversation.** The plugin keeps the question it put in its conversation state and refuses the same one again; the engine no longer counts forks.
- **The library stays, the intake goes.** The knowledge base keeps its read side — search, all, read, text, sources, forget — as the store pair the rail and the host read. Adding a file, and everything before it, leaves with the documents plugin. The invariant that text is kept before a passage is offered belongs to the store pair, not to a caller.
- **The index embeds for itself.** `Host.index` takes text and chunks and embeds with the embedder the search uses, so the two sides cannot diverge.
- **One new event, refusing kind.** `UPLOADING` carries the file's name, runs in the file's field, and a sentence refuses and drops the file. It fires from the upload route alone: a plugin's write, the field-files route and the model's write tool write the same kind of file and announce nothing. The reader's "read this" is the event, not the disk changing.
- **Field files widen to bytes.** Write takes text or bytes, the text read stays text-or-nothing, and a bytes read is new.
- **The intake is one engine function.** Land the file, dispatch, drop on refusal, answer with the name and the field. Both frontends call it.
- **Delegate reads the registry at call time.** The host is handed a late-bound reader of the system-wide tools without effect or asks, plus cora's read; the loop's built-in search goes, and only the answer tool's name stays reserved there.
- **Reserved names are the three tools.** One tool name per registry is already the registry's rule.
- **Refusals are the plugin's sentences.** The plugin's ingestion errors are its own; the core carries one upload refusal the route answers as it answers any refusal.
- **Memory is a tool, a section and a handler.** A store failure raises out of the handler, and the dispatcher's "could not amend the brief" replaces the trace step the domain carried.
- **The brief shrinks to the preamble and the three tools.** The ask rules go to the ask plugin, the search rule to the documents plugin, the memory rule to the memory plugin. The memory plugin and the vocab drill name the fork tool in prose, so they expect the ask plugin loaded.
- **Depth is the plugin's setting.** `CORA_PLUGIN_DOCUMENTS_TOP_K`, default five; `CORA_TOP_K` and the host's depth leave.
- **The contract goes to 2.** A loop written to 1 counted on a search it no longer gets; the shipped interview plugin declares 2.
- **The upload answer stops counting.** It names the document and the field; the page says added, and loses its hint that a duplicate was already there.
- **The reading screen ticks, it does not fork.** Unticked writes through the field-files route, ticked through the upload route. Same file on disk either way.

## Ports, guards and diagrams touched

- Ports: `Host` gains `index` and the upload event; `Files` and `FieldFiles` gain bytes; a new `Index` protocol and a new `Shell` protocol; `Loop` loses its ask slot.
- Domain: `Card` gains the landing name; `MemoryUnread` and the ingestion errors leave; an upload refusal arrives.
- Guards: the gate-and-runtime guard still holds; the no-path-without-gate guard reads a walk with no ask node; packaging names `pypdf` as the documents plugin's; installs and the front door cover three more members; the tool-schema guard reads the plugins' tools.
- Diagrams: round-map and turn-map lose the ask node; upload-map draws intake, event, plugin and index; search-map draws the plugin's tool; domain-map and component-map regenerate.

## Risks / Trade-offs

- [A command tool with no gate on a served agent] → the user's decision, stated here; paths are bounded, the network is not, and the injection screen and the untrusted label are what stand between a document and a command.
- [A bare cora answers with no documents, no memory and no way to ask] → README says so on the first screen, and `make plugins` lists what loaded.
- [Two plugins name the fork tool in prose] → the shipped deployment loads the ask plugin, and the README loop names it first.
- [An edited field file and the document indexed from it diverge] → the document was always a snapshot of the upload; uploading again indexes the new text.
- [Indexed documents in existing stores have no field file behind them] → the rail reads the index, and the file is only where new uploads land.
- [Travel and interview loops search nothing when the plugin is not loaded] → the shipped deployment loads it, and the spec says what a loop gets.

## Migration Plan

- Symlink `ask`, `memory` and `documents` into `.cora/plugins`; the README loop names them.
- No store migration: the index, the text store and the memory table are unchanged.
- Rollback is the branch: trunk takes the change as one squash or not at all.
