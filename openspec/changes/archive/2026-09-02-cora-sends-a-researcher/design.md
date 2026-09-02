## Context

`Host.delegate` already runs a bounded loop and nests its steps, and a loop that spends
its allowance raises rather than reporting — see `proposal.md` for why that is now a limit.

## Goals / Non-Goals

**Goals** — a travel researcher that is pure plugin code. A ceiling that reports instead
of losing what it found. An effect declared on a tool, and withheld from a sub-agent. A
guard over what a sub-agent may be handed.

**Non-Goals** — the approval gate, which is story 11's. A sub-agent that acts or stops to
ask, deferred with a reason. Drawing a nested step, which the shell already does. A
researcher that plans its lookups; the model decides them round by round.

## Decisions

**The ceiling closes out with one model call and no tools.**

- Spending the last round without an answer asks the model to write up what it has.
- No tools are offered on that call, so it cannot dig further and cannot loop.
- The report is prefixed with a sentence saying it stopped early, which the turn reads.
- That sentence states and does not instruct: a report carries the untrusted-data label,
  which tells the model to follow no instruction inside it, so an imperative there is
  addressed to a reader under orders to ignore it. The brief carries the instruction.
- A close-out that comes back empty falls back to today's refusal, so nothing invents a report.
- A loop that gathered nothing is not asked at all, which is what keeps the allowance a
  bound: once the pot is empty every further nested call would otherwise buy a write-up
  the pot never authorised, and the model picks the width of the fan-out.
- Rejected: returning the raw tool messages — a dump is not a report, and the turn would relay it.
- Rejected: silently returning a partial answer — the turn would sign for it as complete.

**An effect is a field on the registration, as untrusted already is.**

- `Tool.effect` and `register_tool(..., effect=True)`, defaulting to changing nothing.
- Story 11 builds the gate on the same field, so nothing about it moves when the gate lands.
- The listing shows it, because "what may this plugin do" is what the listing is for.
- Rejected: a separate registration kind — a tool with an effect is a tool, not a fifth kind.

**A sub-agent is offered a filtered set, and the plugin is told what was withheld.**

- `Host._offered` drops a tool declaring an effect, and logs which on the plugin's own logger.
- Dropped rather than refused: a plugin may reasonably pass its scope's whole tool list.
- Cora's writing and stopping tools stay absent by construction, never put in.
- Rejected: refusing the delegate call — a legitimate caller loses the whole lookup.
- Rejected: dropping in silence — an author would watch their tool never run.

**The guard asks the host, not the list of names.**

- It builds a host, passes it a writing tool, a stopping tool and an effecting one, and reads back what is offered.
- Asserted through the port rather than by naming cora's tools, so a fifth core tool is covered unasked.

**The researcher is a tool that delegates, and nothing more.**

- It is handed the forecast tool rather than building one, because that tool holds an
  HTTP client: one per question would parse the certificate bundle again and reuse no
  connection. One tool serves the turn's registration and every loop.
- Its rounds come from the plugin's settings, capped by the host as any plugin's are.
- A rounds setting it cannot read is a `PluginLoadError` it raises itself, which is the
  one channel that reaches the operator worded: cora keeps any other exception's text
  out of that message, because a plugin's could be carrying a key.
- That also exercises the settings slice story 9 left unexercised, which was recorded as deferred.
- Rejected: a researcher in the core — the whole point is that a sub-agent is someone's plugin.

**What moves at the edges.**

- Ports: `plugin` and `host`, by one field and one keyword, with `CONTRACT` staying 1.
- Guards: a new one over what a sub-agent is offered; the architecture guard stands.
- Diagrams: the component map, by the one import the plugin's own refusal adds. Not the
  round map — that is drawn from the runner's graph, and never drew a delegated loop.

## Risks / Trade-offs

- **The close-out costs a model call beyond the rounds** → one, with no tools, and only when the ceiling is hit.
- **A nested loop that runs out pays a close-out per level** → bounded by nesting, and only
  for a level that gathered something; one that gathered nothing is refused without a call.
- **A caveated report may still be relayed as complete** → the caveat is in the text the turn's model reads, and the brief tells it to say what is unresearched.
- **A withheld tool is a surprise at run time** → logged by name on the plugin's own logger, and stated in the how-to.
- **`effect` ships before its gate** → the field is the contract story 11 needs, and withholding it from a sub-agent is a use of its own.
- **The researcher's quality rests on a real model** → its brief is the only lever, and it is unpinnable by a test.
