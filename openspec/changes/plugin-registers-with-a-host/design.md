## Context

A plugin is a frozen record of four fields, so a fifth kind of contribution changes cora
before it changes the plugin.

## Goals / Non-Goals

**Goals** — a plugin registers against a host, limited by what cora *has* rather than by
what a record declares. One registry, read by the listing, the collision check and the
trace alike. A tool that runs a loop of its own, with its steps shown under the call.

**Non-Goals** — the scope rule that reads a registration, which is story 6. Handlers
taking part in a turn, which is story 5. Markers becoming parents of the steps inside
them, the rest of the nesting shape. Any change to `AgentState`, the pause contract or
the named steps.

## Decisions

**The host is a port, and `extend` is the whole contract.**

- `Host` is a Protocol in `cora.ports.plugin`, and the composition root satisfies it.
- A plugin module defines `extend(cora: Host)` and calls what it needs, returning
  nothing.
- Returning a record would put the shape back — a plugin may only register what a host
  offers.
- The seam is the host: a fifth kind of contribution is a method on it, not a field
  anywhere.

**Registration is one list, and each entry carries the module that made it.**

- Every `register_*` call appends one entry: the module, the kind, and the value.
- The listing, the collision check, the log line and story 6's scope rule read that
  list.
- The kind is a field rather than a class, so a new kind adds an entry and edits no
  switch.
- One place turns the list into what the engine takes: tools, rules and the brief's
  sections.
- That place is a fold per kind, written once, and not a decision repeated per feature.

**What the host offers is what cora has, not a copy of it.**

- Document search, memory and the model reach a plugin as the ports cora itself holds.
- A log and a settings reader come *named for the plugin*, from the module path it
  loaded under.
- Nothing is handed the engine's own steps: a plugin composes cora's parts, it does not
  walk a turn.

**A tool that wants a loop asks the host for one.**

- The host runs a bounded loop over a tool set the plugin passes, and answers with its
  text.
- The set is filtered: a tool that writes or stops is refused a sub-agent, as the shapes
  say.
- The budget is the host's, so a plugin cannot spend a turn's rounds by asking for more.
- Nothing under `src/cora/` is edited to support one: the acid test is a fixture plugin.

**The trace nests where the work nested.**

- A call carries the steps taken inside it, so a sub-agent's rounds hang under its
  `ToolUse`.
- Markers stay flat: turning *screen* and *work* into parents is the same shape, and
  later.

**A refusal names the module, as loading already does.**

- No `extend`, a raise inside it, a taken name — each is a `PluginLoadError` naming the
  module.
- Registration happens at load, so a refusal arrives before a turn rather than during
  one.
- A name is taken if cora offers it or another plugin registered it first, as today.

## Risks / Trade-offs

- **A plugin holds live ports and can call them outside a turn** → it is code the
  deployment named, and the host is the only thing it is handed.
- **`extend` runs arbitrary code at load** → so did importing it, and the refusal names
  the module.
- **A kind as a field invites a switch at the fold** → written once, and guarded by a
  test that every kind reaches the engine.
- **A nested trace widens what is checkpointed and stored** → both find kinds rather
  than listing them, and both are tested against one they have not seen.
- **Both shipped plugins are rewritten with no shim** → they live in this repository,
  and their tests come with them.
- **A sub-agent's loop is slow where a tool was cheap** → its budget is small, and the
  turn's own is untouched.
