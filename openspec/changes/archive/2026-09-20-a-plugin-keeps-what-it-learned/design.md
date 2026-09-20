## Context

`State` is bound to the conversation a turn belongs to and goes when it does. `Memory`
is what cora knows about the user, put in the brief and drawn in a rail. See
proposal.md — Why.

## Goals / Non-Goals

**Goals** — a durable, plugin-owned place for text, reachable wherever the plugin's own
code runs.

**Non-Goals** — documents, which are the reader's and are searched and cited. Anything
shown to the user. A store one plugin can read another's from. Structure: it is text,
and what the text means is the plugin's.

## Decisions

**A port of its own, beside `State` rather than inside it.**

- The two differ in the one thing a caller has to know — how long what they keep lasts —
  and a lifetime passed as an argument is a lifetime somebody gets wrong.
- The shape is deliberately the same, `read` and `keep`, so a plugin author learns one
  thing: which one outlives the conversation.

**It is the store cora already keeps, under a namespace of its own.**

- cora's own SQLite file holds the bookkeeping already, and a second file would be a
  second thing to back up, move and explain.
- The namespace is `("kept", <plugin>)`, so the plugin's name is what separates one
  plugin's names from another's, exactly as the log and the settings are separated.

**Absent rather than empty where there is no store.**

- A deployment assembled without one hands `None`, which a plugin checks, as it checks
  `memory` and `output` already — a store that silently forgot everything would look
  like a plugin bug.

**Text, and nothing about what it means.**

- A plugin that keeps a schedule, a counter or a JSON blob writes and parses its own,
  which is what keeps this port from growing a type system.

## Risks / Trade-offs

- A plugin can fill the file → what is kept is small text by convention rather than by
  a cap, as the settings and the notice are.
- Nothing prunes it → a plugin deleted leaves its namespace behind, which the delete
  can be taught later if it matters.
- Two turns keeping under one name at once → last write wins, as it does for the
  conversation's state.

## Ports, guards and diagrams

- One new port and one adapter over the store the app already builds.
- The architecture guard already holds ports free of technology; nothing new is banned.
- The composition diagram gains a port, and is regenerated from the source it reads.
