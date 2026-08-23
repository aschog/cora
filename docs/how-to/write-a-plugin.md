# Write a plugin

A plugin is how a domain reaches cora: a persona, tools, rules, or any mix of them.
cora imports no plugin of its own, so nothing here edits the engine.

1. **Make the package.** Copy the shape of `plugins/fitness`: a directory under
   `plugins/`, a `pyproject.toml` naming `cora` as its one dependency and
   `module-name = "cora.plugins.<yours>"`, and the module itself under
   `src/cora/plugins/<yours>/`. `plugins/*` is a workspace member, so `uv sync` picks
   the new package up with no edit at the root.

2. **Declare what it contributes.** The module's `__init__.py` defines `PLUGIN`:

   ```python
   from cora.ports.plugin import Plugin

   PLUGIN = Plugin(name="Bird watching", instructions=INSTRUCTIONS, tools=TOOLS)
   ```

   `name` heads the plugin's section of the brief. Everything else is optional — a
   bundle of rules alone is as legitimate as a bundle of tools.

3. **Add a tool, if it has one.** A `Tool` is a name, a description the model reads, a
   JSON Schema for its arguments, and something to call:

   ```python
   from cora.ports.plugin import Tool

   COUNT_TOOL = Tool(
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

4. **Add a rule, if it screens questions.** A `ValidationRule` sees the question alone
   and refuses it before the model is reached.

5. **Name it.** `CORA_PLUGINS` takes module paths separated by commas, in order:

   ```sh
   export CORA_PLUGINS=cora.plugins.security,cora.plugins.birds
   make run
   ```
