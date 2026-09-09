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

   **If calling it changes something outside cora, say that too.** A file written, a
   booking made:

   ```python
   cora.register_tool(name="book_it", ..., run=book_it, effect=True)
   ```

   The listing shows it, in the terminal and in the page's plug menu, because what a
   plugin may *do* is what a reader opens that menu to find out. And cora never offers
   such a tool to a delegated loop: an effect waits for the person watching the turn,
   and a sub-agent is not something they are watching. Pass your whole tool list to
   `delegate` if you like — the ones with an effect are withheld, and your logger says
   which.

   The declaration also buys the gate. A call of your tool does not run on the model's
   word: the turn stops, the user is shown what your tool's `description` says it does
   and the arguments the model wrote, and your `run` is reached only if they approve.
   Decline and it is never called at all — the model is told, and the turn answers
   around it. So write the `description` for the person deciding as much as for the
   model: it is the sentence on the card.

   The gate is cora's, at a point no plugin can subscribe to, and there is nothing a
   handler can return that pauses a turn — which is what keeps it from being something
   a plugin holds. It covers what you *declared*: a tool you registered without
   `effect=True` is not gated, and what your own code does inside any call is the trust
   the deployment extended by loading you.

   **Write what it produces through the output cora hands you.** A path of your own
   would be a path nothing checks:

   ```python
   def extend(cora: Host) -> None:
       if cora.output is None:      # this deployment configured nowhere to write
           return
       kept = cora.output
       def book_it(when: str) -> str:
           return f"Saved to {kept.write('booking.md', when)}"
       cora.register_tool(name="book_it", ..., run=book_it, effect=True)
   ```

   `write` takes a filename and the text, and answers with where the file landed, so
   your tool can tell the user. One place, the deployment's to choose and to move; a
   name that would climb out of it is refused, and the refusal reaches the model as a
   refused call. `cora.output` is `None` where the deployment configured none — register
   no such tool then, the way cora offers no `remember` without a memory. A tool that
   can only fail is worse than one the model is never offered.

   **Ask the user for what the model could not supply.** A tool may declare `asks`: a
   function handed the arguments as written, answering with the card to put to the
   reader — or with `None` to run as called. Build the card out of the schema you
   already declared, so the two cannot drift:

   ```python
   from cora.domain.card import ActionOffered, Card, fields_of, missing_from

   SCHEMA = {"type": "object",
             "properties": {"origin": {"type": "string"},
                            "depart": {"type": "string", "format": "date"}},
             "required": ["origin", "depart"]}

   def asks(arguments: dict) -> Card | None:
       if not missing_from(SCHEMA, arguments):
           return None
       return Card(prompt="Give me the trip and I'll price it.",
                   fields=fields_of(SCHEMA, arguments),
                   actions=(ActionOffered(label="Search", answer="Search",
                                          needs_valid=True),
                            ActionOffered(label="Not now", answer=None)))

   cora.register_tool(
       name="price_it",
       description="Price a trip.",
       parameter_schema=SCHEMA,
       run=price_it,
       asks=asks,
   )
   ```

   A card is a prompt, fields to fill and actions to take, and the page draws whatever
   you hand it: a field's own JSON Schema picks the control, so a date is a date picker
   and a short `enum` is a row of choices, with no frontend of yours anywhere. An
   action's `answer` is what comes back when it is taken, `None` is the way out, and
   `needs_valid` holds it closed until every required field is filled — a page
   affordance, so write the tool to refuse a call it cannot run rather than trusting it.
   What the reader writes is written over the arguments, and your `run` is called once,
   with the values a person stated. Take nothing back but a card: it is data, never
   code, and the page draws every part of it as text.

   **Ask for everything you require.** Cora offers a gathering tool with nothing
   required, because your card is what requires it — a schema telling the model it must
   supply the values says the opposite of the sentence beside it. So leave nothing off
   the card: an argument the schema requires and the card omits is one nobody supplies,
   and the call is refused for want of it.

   **A card asks for two values or more.** cora refuses a card whose writable fields
   come to one, before it is put, and tells the model to ask for that value in its
   answer — so a schema of one property gets no card at all. A call missing one of two
   arguments still gets one: `fields_of` hands back a field per property, so the card
   above stands with two boxes and one of them already filled. Read-only fields are not
   counted, so a card put up to be confirmed rather than filled in is left alone.

   **`asks` has to be pure.** The step that puts your card is replayed every time the
   turn is picked up, so cora calls `asks` again on each of them — always with the same
   arguments, and expecting the same answer. One that reads a clock, a counter or a file
   moves the question the reader already settled, and their answer lands on a different
   one. Do nothing in it but read the arguments and build the card; `run` is where a
   call has an effect. Break, or hand back something that is not a card, and the call is
   refused rather than the turn lost — the model is told and answers around it.

4. **Take part in the turn.** A handler subscribes to a named point in it, is handed
   one frozen value, and answers by returning — a refusal, an amendment, or `None` for
   neither. The five points are `cora.ports.host`'s, and they differ in what a return
   means:

   | Event | Handed | Return | What returning it does |
   | --- | --- | --- | --- |
   | `SCREENING` | the question the user sent | `str` | refuses the turn, with that as the reason |
   | `BRIEFING` | the brief the model is about to read | `str` | replaces it |
   | `CALLING` | a `ToolCall` about to run | `str` | refuses the call, and the model is told why |
   | `RETURNING` | the `ToolResult` that came back | `ToolResult` | replaces what the model is told |
   | `ANSWERING` | the answer, settled and not yet handed over | `str` | replaces what the reader is given |

   `ANSWERING` is where an answer is redacted or rewritten. It replaces what is
   recorded, kept and handed back — but cora streams the model's text to the page as it
   is written, so a reader watching the answer appear has already seen what you removed.
   Treat it as changing the answer that is *kept*, not as holding one back.
   It amends rather than refuses, so blocking one means handing back the sentence they
   should read instead — the turn has already been spent, and throwing it away is a
   worse answer than a substituted one. Citations are read off what you returned, so a
   claim you removed takes its `[n]` with it. It fires once, on the answer, not on
   every model call: the rounds before the last are thinking, and their prose is on the
   trace, which a redaction here does not reach.

   Return the type in that column or `None`. Anything else is dropped exactly as a raise
   is — a `RETURNING` handler answering with a string changes nothing, and a `SCREENING`
   handler answering with something that is not a sentence refuses on cora's wording
   rather than on your value. A `RETURNING` handler is read for the payload and the
   error: the call id answers one call and is not yours to change. Two things `CALLING`
   does not cover: either of cora's asks — `ask_user` and `ask_user_for` — which the
   turn settles with the reader before the tools run, and the arguments — you are handed
   a copy, so rewriting them changes nothing.

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

   `cora.state` is what your plugin keeps between the turns of one conversation — a
   plan it worked out, a count it is running, a form half filled in. Names are your
   own, values are text, and a name nothing was kept under reads as nothing. It lasts
   as long as the conversation and goes when it is deleted, which is what makes it a
   different thing from `cora.memory` — that is what cora knows about the *user*, and
   it outlives every conversation. Reachable while one of your tool calls is running;
   outside one there is no conversation to keep anything for, so a read comes back with
   nothing and a write is dropped.

   ```python
   def counted(cora: Host) -> str:
       so_far = int(cora.state.read("wrens") or 0) + 1
       cora.state.keep("wrens", str(so_far))
       return f"{so_far} wrens this conversation"
   ```

   `CORA_PLUGIN_BIRDS_UNITS=imperial` reaches `cora.plugins.birds` as `units`. Cora's
   own `CORA_` variables are a separate namespace, and two plugins whose module paths
   end in the same segment are refused rather than sharing one.

   A credential is a setting like any other, and it is yours to keep out of the answer:
   put it on the request and never in what you return, because a tool's result is read
   by the model and written to the trace. Check where your HTTP client logs, too: a
   credential that travels in a query string is in the URL, and a client that logs the
   URL it fetched will put it in the operator's console. Register the tool it belongs to only where
   the setting is actually set — the travel plugin offers its two price searches only
   when `CORA_PLUGIN_TRAVEL_SERPAPI_KEY` is there, because a tool the model can call
   and that can only fail is worse than one it was never offered.

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
   call, so a turn that makes several spends several caps. A loop that reaches the cap is
   asked once more, with no tools, to write up what it found — so the rounds it spent
   are not lost, and what comes back says it stopped early rather than reading as a
   whole answer. Only a write-up that comes back empty fails the call. What it did is
   shown under the call that ran it, and what it answers carries no `[n]` — citation
   numbers belong to the turn. Because it read the user's documents, its answer reaches
   cora's own model labelled untrusted, the same as a passage would.

   Work your *own* code does leaves nothing on the trace unless you say so. `cora.show`
   puts one line there — what you just did, detail behind it for a reader who opens it,
   and whether it went wrong:

   ```python
   cora.show("priced 8 departures", detail="cheapest was 2026-09-08")
   ```

   Cora fills in which plugin said it, so a line can never carry another plugin's name.
   It lands among the steps of the call it was said inside, beside a delegated loop's
   rounds; said outside a call there is nothing to report to and it is dropped. A line
   marked as gone wrong is shown as failed and does not end the turn.

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
   calls — including a tool's `untrusted` and `effect` — `Host.output` and the `Output`
   port it hands back, `Host.state` and the `State` port it hands back, `Host.show`,
   the five event names,
   `CONTRACT`, `DEFAULT_SCOPE`, and the values a handler is handed — `ToolCall` and
   `ToolResult` from `cora.ports.plugin`, `ToolRefusal` to raise when a call cannot
   run, and `PluginLoadError` from `cora.domain.errors` to raise while registering when
   the deployment has configured you wrongly — that one reaches the operator as you
   worded it, where any other exception reaches them as its class name alone. **What
   may move** is everything else: `cora.engine`, `cora.app`, the shape of the trace, and the
   wording of any message. A compatibility policy waits for the first
   author it would bind; until then, the version is how you find out — with one gap
   worth knowing: the contract grows keywords without the number moving, so a plugin
   passing `untrusted` or `effect` to an older cora fails on the call rather than at the
   version check. The number tells you about a contract that *changed*, not one that
   grew.

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

   A plugin that has grown past one file drops in the same way: copy its folder — a
   directory holding `__init__.py` — and it is one plugin named for the folder, its
   relative imports working as written. Either shape may import anything installed;
   nothing is installed *for* it, so a dependency cora's environment lacks is a refusal
   naming the plugin. A plugin that wants dependencies of its own is a package, which
   is step 1.

   The folder is live: a plugin dropped while cora serves is installed by the next
   request, a deleted one is removed, and an edited one serves its new code — reload
   the page, no restart. The field it registers under arrives with it and leaves with
   it, and a symlink counts as its target — a plugin still being written deploys by
   `ln -s` and edits live. A drop that cannot load refuses that request readably and
   what was already loaded keeps serving.

10. **See what loaded.** `make plugins` prints every plugin under where it came from,
    with what each registered and the scope it applies in — and a registration carrying
    no scope is marked `system-wide`, because a claim on every turn is a visible act:

    ```sh
    make plugins
    ```

    `GET /api/plugins` carries the same listing. Both read the registrations the
    running app holds, so neither can drift from what it describes.
