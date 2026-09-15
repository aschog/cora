## Context

A delegated loop hands back prose, and its one caller finds a JSON day shape in it by
hand (see proposal.md — Why).

## Goals / Non-Goals

**Goals:**

- One seam for a declared shape, reached by every plugin without a contract bump.
- A shape the model did not satisfy is a refusal with a reason, never a default value.
- No new provider mechanism: the shape rides one cora already sends and already checks.

**Non-Goals:**

- The turn's own rounds, which ask for tool calls and read prose as the answer.
- `response_format` / `with_structured_output`: see the decision below.
- Probing what a model supports, or routing to one that does.

## Decisions

- **A declared shape is one more tool the loop is offered, named `answer`, whose
  parameter schema is the shape.** A tool schema *is* a provider-enforced JSON Schema,
  sent as a schema and not described in words.
- That reuses three things whole: the provider's own function-calling enforcement,
  `ToolRuntime`'s argument validation, and its `invalid arguments:` result — which the
  model reads and corrects on its next round, at no new cost.
- It also fits the north star: an entry added at an existing extension point, where a
  parameter on the model port would widen a Protocol six implementations are typed
  against and touch the adapter, the debug wrapper and four hand-written fakes.
- **Rejected: OpenRouter `response_format` with a JSON Schema.** Support is per
  endpoint, and a provider without it has the parameter *silently ignored* — the schema
  asked for in words, which is the failure this change exists to remove.
- Rejected with it: `with_structured_output`, which cannot carry a top-level array,
  rewrites the caller's schema in place under `strict`, breaks the adapter's streaming
  path, and whose parser validates nothing at all.
- **The loop returns when the `answer` call comes back clean**, so a shaped answer costs
  no round an unshaped one does not — the answering round is the tool-bearing round the
  loop already ends on.
- Rejected: a dedicated shaped round after the loop goes final. The pot is spent before
  the reply arrives, so a loop that answered on its last round would be refused for
  having no round left to shape in.
- **`delegate` is overloaded, not doubled**: no shape returns prose as today, a shape
  returns the validated `dict`. The overloads are declared on the port and repeated on
  the implementation, which is what the type checker asks of a Protocol member.
- Rejected: a result object with `.text` and `.value` — that changes a return type every
  plugin is typed against, which the versioned contract counts as a break.
- **A shape must be valid JSON Schema and must require something**, refused before a
  round is spent. Without a root `required`, an empty object satisfies the shape and the
  change ships inert.
- **Every failure of a shaped call is a `ToolRefusal`**: prose where the shape was
  asked for, an overspent loop, an unusable shape. Three sentences, told apart.
- A shaped loop does not close out with `STOPPED_EARLY` prose, because a heading cannot
  be glued onto a value.
- Strings inside the returned value are stripped of citation runs, the invariant
  `_uncited` already holds for prose: a `[1]` reaching the turn's transcript would draw
  the reader a button onto an unrelated passage.

## Risks / Trade-offs

- A model can emit tool arguments that never parse, which ends the turn as any malformed
  tool call does → the shaped path turns the failures that are about *this answer* into
  refusals, and lets the ones about the provider propagate.
- `Draft202012Validator` ignores `format`, so a shape saying `date` does not mean the
  dates parse → the planner keeps reading its own dates, and a test says so.
- A model that writes prose instead of calling `answer` refuses rather than being
  nudged → one refusal costs the caller a call, and a nudge round is the upgrade path if
  models turn out to need it.
- A plugin tool named `answer` is refused rather than shadowed, as cora's search already
  is → a name the plugin can change, said in a sentence.
- The travel planner loses two revision passes for a refusal, where empty days used to
  revise → empty days still revise; only a refusal ends the call.

## Migration Plan

Nothing changes for a caller that declares no shape, so both existing callers and every
fake keep working; the planner moves to the shape in the same change.

## Diagrams and guards

- No diagram changes: the round map draws the turn's own rounds, not a delegated loop's,
  and the six were regenerated to confirm it.
- The architecture guard is untouched: `jsonschema` is already its one exemption, and no
  provider name goes near the engine.
