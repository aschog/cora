## Context

A tool that reaches outside cora has no way to say so, and `Citable` is the only door to
the untrusted label — see `proposal.md` for why that is now a limit.

## Goals / Non-Goals

**Goals** — a travel tool that fetches a forecast. A tool that declares what its result
is. That declaration earning the untrusted label. A failure out there costing one call.
A plugin allowed the technology its own manifest buys.

**Non-Goals** — a citation for what was fetched, the trace being the record instead. A
credential, the service needing none. A cache, a retry or a rate limiter. A second
service. Any change to `Citation`, to what is stored, or to the page.

## Decisions

**A tool declares what its result is, once, at registration.**

- `register_tool` takes one more keyword, and `Tool` carries it as a field.
- Reaching outside is a property of the tool, not of a call or of a payload's shape.
- It is the move stories 10 and 11 both make: a mark is a field on a registration.
- Rejected: a wrapper the tool returns — a plugin would learn a class to hand back a string.

**The label lands where the call is made, through what is already there.**

- `ToolRuntime.execute` calls `nesting.read_untrusted()` when a declaring tool has run.
- `ToolStep` already reads `inside.untrusted` for a payload that is not `Citable`.
- A tool that delegates still earns the label dynamically, and the two agree rather than compete.
- Rejected: a second branch in `ToolStep` on the payload's type — a switch where a field will do.

**`Citable` stays what it is, and a forecast is not one.**

- A fetched result hands out no numbers, so there is nothing a `Citable` would give it.
- Rejected: renaming `Citable` to a material abstraction with a non-citing kind — the more
  correct shape, at the cost of a rename across the engine and a public surface this
  change does not need.

**The label's wording names a service.**

- It says "the user's documents, or a tool that read them", and now a service too.
- One wording over both, because what the model is told to do about it is the same.

**The tool renders one line.**

- For a payload that is not `Citable`, the trace's line and the model's message are one text.
- So the forecast is one line: the place, the dates, and a high, a low and a word per day.
- Cost: a longer forecast would want that split, which is the rejected abstraction above.

**The travel tool is two calls to one keyless service.**

- Open-Meteo: a place name resolved to coordinates, then a forecast for those dates.
- The plugin owns its HTTP client, its timeout and the shape it renders.
- Rejected: a keyed service — a reviewer without a key would only ever see the failure line.

**A failure is a `ToolRefusal`, which the runtime already knows what to do with.**

- A refusal is quoted to the model as that call's result, and the trace shows it failed.
- Rejected: any other exception — only its kind reaches the model, which is no friendly line.

**A plugin's technology is keyed per plugin and bought by its own manifest.**

- `PLUGIN_TOOLKITS` mirrors `FRONTEND_TOOLKITS`, with the same manifest-buys test beside it.
- The packaging guard's `== {"cora"}` becomes the app plus what that plugin declares.
- Rejected: one set for the layer — every plugin would inherit an HTTP client it never asked for.

**What moves at the edges.**

- Ports: `plugin` and `host`, by one field and one keyword, with `CONTRACT` staying 1.
- Guards: the architecture and packaging allow-lists.
- Diagrams: none. No domain class moves, and the assembly is untouched.

## Risks / Trade-offs

- **A current fact cannot be verified from the answer** → the trace names the call and what
  came back, which is what was chosen over a citation.
- **A live service makes a test flaky** → the boundary is stubbed, and the real call is an
  `integration` test.
- **Open-Meteo's shape could change under us** → a shape the tool cannot read is the failure line.
- **The trace's line is the whole payload** → the tool renders one line, and a longer forecast
  is what would earn the split.
- **The untrusted label now has two sources** → both set one flag, so they OR rather than compete.
