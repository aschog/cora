## Context

Only a delegated loop reports what it did, so a plugin that runs its own control flow
is a silence between a call and its result.

## Goals / Non-Goals

**Goals** — one line a plugin contributes, named for it, landing under the call it
happened in, and read back exactly as every other step is.

**Non-Goals** — a plugin building the engine's own kinds of step, which would let it
forge a model decision. Nesting a plugin's lines under each other, until a plugin has a
tree worth showing. Reaching the reader while the call is still running, which is the
whole page and not this.

## Decisions

**One more kind of step, and the plugin fills in only what it knows.**

- The kind carries the plugin, the line, the detail and whether it went wrong, which is
  what `HandlerRan` already carries for a handler.
- `step_kinds` finds subclasses, so the checkpoint, the conversation store and the wire
  learn it without an edit anywhere.
- Rejected: a plugin passing a `TraceStep` — the one shape it must not be able to write
  is a step claiming the model decided something.

**The host signs it, because only the host knows who is asking.**

- `PluginHost` holds the module it was built for, and already names the logger and the
  settings from it.
- The name a plugin passes is not read, so the signature is cora's own rather than a
  convention plugins keep.

**It lands through the collector that is already there.**

- `cora.engine.nesting.took` puts a step under the call being collected, and drops it
  where there is none.
- So "under the call" and "dropped outside one" are the existing behaviour, reached by
  one more caller rather than written again.

**Named `show`, in the imperative the rest of the contract is written in.**

- `register_tool`, `register_handler`, `delegate` — a verb the plugin author is telling
  cora to do.

## Risks / Trade-offs

- A plugin can put anything in the line, and a reader takes the trace at face value —
  the same trust that loading the plugin already extended.
- A loop that shows a line per iteration can make a long trace, which is the plugin
  author's judgement rather than a cap cora imposes.
- The line still only reaches the reader when the call returns, so a slow call is a slow
  trace.

## Ports, guards and diagrams

- `Host.show` as added surface, so `CONTRACT` stands where it is.
- No new port, and no adapter: the collector and the trace are both already there.
- The domain class diagram is regenerated, because the trace gains a kind.
