# Write a plugin

A plugin is how a domain reaches cora: a persona, tools, a hand in the turn itself, or
any mix of them. cora imports no plugin of its own, so nothing here edits the engine.

1. **Make the package.** Copy the shape of `plugins/fitness`: a directory under
   `plugins/`, a `pyproject.toml` naming `cora` as its one dependency and
   `module-name = "cora.plugins.<yours>"`, and the module itself under
   `src/cora/plugins/<yours>/`. `plugins/*` is a workspace member, so `uv sync` picks
   the new package up with no edit at the root.

2. **Register what it has.** The module's `__init__.py` defines `extend`, which cora
   calls once with a host of its own:

   ```python
   from cora.ports.host import SCREENING, Host

   def extend(cora: Host) -> None:
       cora.register_instructions(INSTRUCTIONS)
       cora.register_handler(event=SCREENING, handle=refuse_out_of_season)
   ```

   Register as much or as little as you have. A plugin of one handler is as legitimate
   as a plugin of tools, and one that registers nothing loads and contributes nothing.
   Your instructions become a section of the model's brief, headed by your module.

3. **Add a tool, if it has one.** A tool is a name, a description the model reads, a
   JSON Schema for its arguments, and something to call:

   ```python
   cora.register_tool(
       name="count_species",
       description="How many species were seen on a given day.",
       parameter_schema={
           "type": "object",
           "properties": {"day": {"type": "string"}},
           "required": ["day"],
       },
       run=count_species,
   )
   ```

   The name has to be free: cora refuses a plugin that takes one of its own tool names,
   or one another loaded plugin registered first, and the refusal names your module.

   **If your tool reaches outside cora, say so.** A service you called, a page you read
   — that is material cora did not write, and it must not reach the model as though it
   had:

   ```python
   cora.register_tool(name="fetch_forecast", ..., run=fetch_forecast, untrusted=True)
   ```

   What such a tool returns arrives behind the same untrusted-data label a passage of
   the user's own documents carries, telling the model to read it as evidence and never
   to follow instructions found inside it. Declared on the tool rather than worked out
   from what you return, because a fetched string and a calculated one are the same
   shape and only you know which is which — and no handler, yours or anyone's, can take
   the label off once it is on. A tool that reaches outside also owns what it reaches
   with: your own client, your own timeout, and a `ToolRefusal` in one friendly sentence
   when the service is down, so the turn answers around it rather than ending.

   Nothing cora hands back for a fetched result is citable: `[n]` opens onto a passage
   of a document the user uploaded, and a service has none. Report what you fetched in
   prose, and let the trace be the record of the call. Your `ToolRefusal` is labelled
   too, so quoting a service in one is safe.

4. **Take part in the turn.** A handler subscribes to a named point in it, is handed
   one frozen value, and answers by returning — a refusal, an amendment, or `None` for
   neither. The four points are `cora.ports.host`'s, and they differ in what a return
   means:

   | Event | Handed | Return | What returning it does |
   | --- | --- | --- | --- |
   | `SCREENING` | the question the user sent | `str` | refuses the turn, with that as the reason |
   | `BRIEFING` | the brief the model is about to read | `str` | replaces it |
   | `CALLING` | a `ToolCall` about to run | `str` | refuses the call, and the model is told why |
   | `RETURNING` | the `ToolResult` that came back | `ToolResult` | replaces what the model is told |

   Return the type in that column or `None`. Anything else is dropped exactly as a raise
   is — a `RETURNING` handler answering with a string changes nothing, and a `SCREENING`
   handler answering with something that is not a sentence refuses on cora's wording
   rather than on your value. A `RETURNING` handler is read for the payload and the
   error: the call id answers one call and is not yours to change. Two things `CALLING`
   does not cover: an `ask_user` call, which the turn settles with the reader before the
   tools run, and the arguments — you are handed a copy, so rewriting them changes
   nothing.

   ```python
   def a_note_on_the_season(brief: str) -> str:
       return f"{brief}\n\nIt is nesting season, so answer with that in mind."

   def no_ringing_records(call: ToolCall) -> str | None:
       if call.name == "count_species" and call.arguments["day"] == "today":
           return "today's records are not in yet, so ask for yesterday"
       return None
   ```

   Handlers on one event run in load order, each amendment handed what the one before it
   returned, and the trace names your plugin for every one it made. A handler that
   raises where the event refuses — `SCREENING`, `CALLING` — refuses anyway, because a
   broken check must not admit anything. One that raises anywhere else is dropped and
   the turn carries on without it. Nothing a handler was holding reaches the user or the
   model: only the kind of what it raised is passed on.

5. **Scope it, if it belongs to one part of the app.** Every registration takes a
   `scope`, and one given none applies to every turn:

   ```python
   cora.register_instructions(INSTRUCTIONS, scope="birds")
   cora.register_tool(name="count_species", ..., scope="birds")
   cora.register_handler(event=SCREENING, handle=refuse_out_of_season)
   ```

   A turn running under `birds` gets the persona and the tool, and a turn running under
   anything else gets neither. The screen above is system-wide, and nothing a turn is
   running under can switch it off — which is what a safety check needs.

   Which fields a turn *may* run in is the deployment's to say, in `CORA_SCOPES`. Which
   of them it does run in is the turn's: a pinned conversation is answered in its field,
   and an unpinned one has its question read for the field it belongs to. The first line
   of your instructions is what the router is given to choose between, and what the card
   that asks the reader says under your scope's name — so open by saying what the field
   answers, not with a rule.

6. **Use what cora has.** The host is cora as your plugin is handed it — the documents
   the user uploaded, what cora remembers, the model behind every turn, a log named for
   your plugin, and the settings named for it in the environment.

   `cora.documents.search` reads the field the turn is running in, not every field there
   is. You are not handed that field and cannot ask for another: a plugin cannot see the
   turn it is in, so cora binds it around every point your code runs — a tool call, a
   handler, a delegated loop — and the search reads it from there. A passage from a field
   the turn is not in is a passage its answer could never cite.

   ```python
   def extend(cora: Host) -> None:
       units = cora.settings.get("units", "metric")
       cora.log.info("bird watching is on, in %s", units)
   ```

   `CORA_PLUGIN_BIRDS_UNITS=imperial` reaches `cora.plugins.birds` as `units`. Cora's
   own `CORA_` variables are a separate namespace, and two plugins whose module paths
   end in the same segment are refused rather than sharing one.

7. **Let a tool run a turn of its own.** `cora.delegate` runs a bounded loop with the
   model, offered the tools you pass it and cora's document search:

   ```python
   def extend(cora: Host) -> None:
       def research(question: str) -> str:
           return cora.delegate(question, rounds=2)

       cora.register_tool(name="research", description=..., parameter_schema=..., run=research)
   ```

   The tool closes over the host it was registered against, which is how it still has a
   cora to delegate to by the time the model calls it.

   The loop is offered your tools and cora's document search, and none of cora's own
   tools that write or stop the turn — an effect and a stop-to-ask belong in the turn,
   where the gate is. It is bounded rather than sandboxed: a tool *you* pass it is a tool
   it can call, and `rounds` is capped by the host whatever you ask for. The cap is per
   call, so a turn that makes several spends several caps. What it did is shown under the
   call that ran it, and what it answers carries no `[n]` — citation numbers belong to the
   turn. Because it read the user's documents, its answer reaches cora's own model
   labelled untrusted, the same as a passage would.

8. **Say which contract it wants.** cora offers one version at a time, and a plugin
   names the one it was written against:

   ```python
   CONTRACT = 1
   ```

   Write the number, not an import of cora's own `CONTRACT` — importing it would
   declare whatever the cora in front of you offers, which is the check saying yes to
   everything.

   It is read before `extend` is called, so a plugin cora will not have never runs. A
   plugin declaring nothing is taken as asking for the version cora offers, and one
   asking for another is refused by name — the refusal says which version it wanted and
   which cora has.

   **What is public** is everything `cora.ports.host` names: `Host` and its register
   calls — including a tool's `untrusted` — the four event names, `CONTRACT`,
   `DEFAULT_SCOPE`, and the values a handler is handed — `ToolCall` and `ToolResult`
   from `cora.ports.plugin`, and `ToolRefusal` to raise. **What may move** is everything
   else: `cora.engine`, `cora.app`, the shape of the trace, and the wording of any
   message. A compatibility policy waits for the first
   author it would bind; until then, the version is how you find out.

9. **Load it.** Two ways, and neither is a fork. Name the module in `CORA_PLUGINS`,
   separated by commas, in order:

   ```sh
   export CORA_PLUGINS=cora.plugins.security,cora.plugins.birds
   make run
   ```

   Or drop a single `.py` file into `./.cora/plugins/` and skip the packaging entirely:

   ```sh
   cp field_notes.py .cora/plugins/
   make run
   ```

   A dropped file is named for itself — `field_notes.py` is the `field_notes` plugin,
   which heads its section of the brief and names its settings. The name has to be a
   plain identifier, because it also spells a variable in the environment. The folder is
   read in name order after the modules `CORA_PLUGINS` names, because load order is the
   only precedence there is, and `CORA_PLUGINS_PATH` moves the folder.

   A dropped plugin is *one* file: it may import anything installed, but it cannot
   import a neighbour in the folder or use a relative import. A plugin that has grown
   past one file is a package, which is step 1.

10. **See what loaded.** `make plugins` prints every plugin under where it came from,
    with what each registered and the scope it applies in — and a registration carrying
    no scope is marked `system-wide`, because a claim on every turn is a visible act:

    ```sh
    make plugins
    ```

    The same listing is behind the plug icon on the page. Both read the registrations
    the running app holds, so neither can drift from what it describes.
