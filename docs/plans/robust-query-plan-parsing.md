# Robust query-plan parsing

Advanced retrieval asks the model for "JSON only", but `parse_plan` does a bare
`json.loads`. Real models wrap the JSON in ```` ```json ```` fences or prose, so parsing
throws, `QueryPlanner.plan` falls back to a single query, and advanced mode silently
degrades to plain — no error, no failing test. Make the parser tolerant of the wrapping.

## Acceptance criteria

- A fenced or prose-wrapped but structurally valid reply parses into the correct
  `QueryPlan` (queries + optional `source` filter).
- A reply with no recoverable JSON object still returns `None` → single-query fallback.
- Bare-JSON replies and every existing advanced-rag test are unchanged.

## Design

- Change lives entirely in the pure `parse_plan` (`query_planner.py`); port, adapter,
  fakes and `LoggingChatModel` untouched.
- Add a pre-parse extraction ahead of the unchanged `json.loads` + structural check:
  strip a Markdown fence if present, else take the first balanced `{…}` (quote/escape
  aware so braces inside strings don't miscount).
- Extraction only unwraps — it never repairs malformed JSON. No candidate, or a
  candidate that still fails to parse/validate, → `None`, exactly as today.

## TDD checklist

- [ ] a ```` ```json ```` fenced object parses into the expected queries (was `None`).
- [ ] an untagged ```` ``` ```` fence parses too; leading/trailing prose parses.
- [ ] a wrapped reply with a valid `source` still yields the `MetadataFilter`.
- [ ] braces inside a query string don't truncate the balanced scan.
- [ ] genuinely non-JSON, and fenced-but-malformed JSON, still return `None`.
- [ ] a bare valid JSON object parses exactly as before (regression guard).

## Fallout

None expected — behaviour-preserving on inputs that already parsed, only widening the
wrapped ones. `response_format`/JSON-mode is the durable fix but touches the port; left
as a future knob. Confirm gates green.
