## Context

A plugin cannot see the turn it runs in, so anything it works out has to travel back
through the model as text or be lost.

## Goals / Non-Goals

**Goals** — one store a plugin reads and writes by name, held per conversation and per
plugin, and dropped with the conversation it belonged to.

**Non-Goals** — a store keyed by the user, which is what cora's memory already is. A
shape richer than text, which would make cora the reader of what a plugin kept. A quota,
because a plugin is code the deployment chose to run. State a handler can reach, until a
handler needs it.

## Decisions

**It rides the turn's state, because the checkpointer already keeps one per thread.**

- `AgentState` gains one key, and the saver a deployment already configured persists it
  beside the messages and the trace.
- Deleting a conversation drops the thread, and what rode on it goes without a line of
  code.
- Values are text, so the serialiser needs no entry in the checkpointed types.
- Rejected: a port and a sqlite adapter of its own — a second thing keyed by thread,
  which the checkpointer is, and a second thing to delete in step with the first.

**The key is never seeded per turn, which is the bug this shape invites.**

- `filled` is emptied at the top of each turn because it belongs to one; this does the
  opposite, and a test says so.

**A call reads a snapshot and its writes are collected, as a card's values are.**

- The tool step binds what plugins kept before the call and collects what the call
  wrote, the way `cora.engine.nesting` collects the steps a call took.
- It merges them into state when the call is done, as the gate step merges a card's
  values into `filled` before it.
- A delegated loop inside the call sees the same snapshot, because it is inside the same
  binding.
- Rejected: a tool returning a state update — cora calls tools by keyword and reads a
  payload, and threading LangGraph's `Command` into that would put the graph in the
  plugin contract.

**No thread id reaches a plugin, and none needs to.**

- The state is already this conversation's by the time the step holds it, so a plugin
  names a key and never a conversation.

**The host namespaces, because only the host knows which plugin is asking.**

- `PluginHost` holds the module it was built for, and already reads settings under that
  name.

**Nothing is kept outside a tool call.**

- A read comes back with nothing and a write is dropped, as `took` drops a step taken
  outside a call.
- Rejected: raising — a plugin doing housekeeping at load would fail the deployment.

## Risks / Trade-offs

- What a plugin keeps grows the checkpoint, and a plugin that writes a lot makes every
  later turn's state larger.
- Text values mean a plugin serialises its own shape, which is a parse it has to defend.
- Two turns of one conversation answering at once could overwrite each other, which cora
  does not offer today and does not start to here.

## Ports, guards and diagrams

- `Host.state` as added surface, so `CONTRACT` stands where it is.
- No new port and no new adapter, so the component map is unchanged.
- The domain class diagram is regenerated, because `AgentState` gains a key.
- The round diagram is regenerated, because the tool step gains a binding it follows.
