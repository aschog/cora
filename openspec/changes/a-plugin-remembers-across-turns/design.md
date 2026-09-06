## Context

A plugin cannot see the turn it runs in, so anything it works out has to travel back
through the model as text or be lost.

## Goals / Non-Goals

**Goals** — one store a plugin reads and writes by name, held per conversation and per
plugin, and dropped with the conversation it belonged to.

**Non-Goals** — a store keyed by the user, which is what cora's memory already is. A
shape richer than text, which would make cora the reader of what a plugin kept. A quota,
because a plugin is code the deployment chose to run. State a handler can reach, until
a handler needs it.

## Decisions

**The conversation is bound around the call, the way its fields already are.**

- `cora.engine.scoping` gains the thread beside the scopes, bound at the one place the
  scopes are bound, so nothing new decides when a plugin is inside a turn.
- `AgentState` carries the thread, seeded where the question is, because a step reads
  state and never the runner's config.
- Rejected: binding it around the whole run — the stream is a generator, and a context
  entered across a yield leaks into whoever is iterating.

**A port, because the confinement is cora's rather than each plugin's.**

- `State` is two verbs: read a name, and keep text under one, where keeping nothing
  drops it.
- The plugin names a key and never a conversation, so no plugin can read another
  conversation by guessing at its id.
- Rejected: handing a plugin a directory — every plugin would write the same keying and
  confinement check, and each would be a different bug.

**The host namespaces, because only the host knows which plugin is asking.**

- `PluginHost` already knows its module, and already reads settings under that name.
- The store sees a key the host built, so a plugin cannot spell its way into another's.

**It is kept where the conversation's turns are kept.**

- One sqlite file holds the turns, the checkpoints and now this, so a deployment that
  deletes it loses a whole conversation rather than half of one.
- `Agent.forget` drops it beside the turns and the thread, which is the rule that file
  already states.

**Nothing is kept outside a turn.**

- A read comes back with nothing and a write is dropped, as `took` drops a step taken
  outside a call.
- Rejected: raising — a plugin doing housekeeping at load would fail the deployment for
  it.

## Risks / Trade-offs

- Text values mean a plugin serialises its own shape, which is a parse it has to defend.
- A conversation that is never deleted keeps what its plugins wrote for as long as it
  lives, which is the same promise its turns have.
- Two turns of one conversation answering at once could overwrite each other, which cora
  does not offer today and does not start to here.

## Ports, guards and diagrams

- New port `cora.ports.state`, and `Host.state` as added surface, so `CONTRACT` stands.
- The component map is regenerated, because assembly binds one more adapter.
- The architecture guard is unchanged: a protocol states a shape and holds no data.
