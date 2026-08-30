# Write a plugin

A plugin is how a domain reaches cora: a persona, tools, rules, or any mix of them.
cora imports no plugin of its own, so nothing here edits the engine.

1. **Make the package.** Copy the shape of `plugins/fitness`: a directory under
   `plugins/`, a `pyproject.toml` naming `cora` as its one dependency and
   `module-name = "cora.plugins.<yours>"`, and the module itself under
   `src/cora/plugins/<yours>/`. `plugins/*` is a workspace member, so `uv sync` picks
   the new package up with no edit at the root.

2. **Register what it has.** The module's `__init__.py` defines `extend`, which cora
   calls once with a host of its own:

   ```python
   from cora.ports.host import Host

   def extend(cora: Host) -> None:
       cora.register_instructions(INSTRUCTIONS)
       cora.register_rule(SeasonRule())
   ```

   Register as much or as little as you have. A plugin of rules alone is as legitimate
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

4. **Use what cora has.** The host is cora as your plugin is handed it — the documents
   the user uploaded, what cora remembers, the model behind every turn, a log named for
   your plugin, and the settings named for it in the environment:

   ```python
   def extend(cora: Host) -> None:
       units = cora.settings.get("units", "metric")
       cora.log.info("bird watching is on, in %s", units)
   ```

   `CORA_PLUGIN_BIRDS_UNITS=imperial` reaches `cora.plugins.birds` as `units`. Cora's
   own `CORA_` variables are a separate namespace, and two plugins whose module paths
   end in the same segment are refused rather than sharing one.

5. **Let a tool run a turn of its own.** `cora.delegate` runs a bounded loop with the
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

6. **Name it.** `CORA_PLUGINS` takes module paths separated by commas, in order:

   ```sh
   export CORA_PLUGINS=cora.plugins.security,cora.plugins.birds
   make run
   ```
