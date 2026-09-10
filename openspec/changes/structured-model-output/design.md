## Context

A delegated loop hands back the model's prose, and its one caller finds a JSON day shape
in it by hand (see proposal.md — Why).

## Goals / Non-Goals

**Goals:**

- One seam for a shape, on the model port, so every plugin gets it without a change.
- A shape that cannot be had is an error with a reason, never a value read loosely.
- LangChain stays behind the adapter, as the architecture guard requires.

**Non-Goals:**

- The turn's own rounds: cora asks for tool calls there, and reads prose as the answer.
- A schema language of cora's own — the model port already speaks JSON Schema.
- Probing what a model supports before a run, or routing to one that does.

## Decisions

- The shape is a parameter on `complete`, not a second port method, because a round
  either carries one or does not and everything else about it is the same.
- It crosses the port as a plain JSON Schema mapping, the shape `Tool.parameter_schema`
  already is, so no provider type or model class reaches the engine.
- Only the answering round carries it: the loop keeps its tool rounds untouched, and the
  shape is asked for in the write-up round `delegate` already runs with no tools.
- That reuses an existing path rather than adding one, and sidesteps asking a provider
  for tools and a schema in the same call.
- The adapter binds it through LangChain's structured-output runnable over OpenRouter's
  `json_schema` response format, keeping the raw reply so a failure is readable.
- A provider that will not take a schema raises cora's model error, naming the model: no
  retry helps, and a deployment must hear it rather than read prose that looks fine.
- An answer that does not satisfy the shape is asked for once more, then refuses the
  call — the same shape as the loop that gathered nothing, so the turn survives it.
- The refusal is what makes this worth doing: the failure the change removes was silent,
  so nothing here may end in a default value.
- `delegate` keeps returning prose where no shape was declared, so every plugin that
  reads a sentence is untouched and this needs no plugin contract bump.

## Risks / Trade-offs

- The provider is trusted to enforce the schema it accepted → cora checks the answer
  parsed and rejects a reported parse failure, and a validator dependency is the upgrade
  path if that proves thin.
- `json_schema` support varies by model, so a deployment can be one model change away
  from a broken plugin → the error names the model, and the docs say the tier is live.
- A retry doubles the cost of a bad answering round → one retry only, inside the
  allowance the loop already spends.
- The travel planner loses its tolerance for prose, so a model that used to produce a
  dayless plan now fails a call → what the reader sees is a failed call with a reason,
  which is the point.

## Migration Plan

The port gains an optional parameter, so both fakes and both adapters keep working; the
planner moves to the shape in the same change, and nothing else calls with one.

## Diagrams and guards

- `docs/assets/component-map.svg` and `docs/assets/round-map.svg` — regenerate if the
  port's own line changes.
- The architecture guard stays as it is: LangChain names must not appear outside the
  adapters.
