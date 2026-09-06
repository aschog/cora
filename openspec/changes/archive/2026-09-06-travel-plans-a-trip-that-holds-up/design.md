## Context

The model calls a tool, reads the answer and writes prose, so nothing tests whether the
trip it described actually holds together.

## Goals / Non-Goals

**Goals** — a planning loop the plugin owns, a plan the plugin holds as a shape, checks
that are arithmetic rather than opinion, and a revision the loop decides to make.

**Non-Goals** — a solver: the search is over candidate departures, not over every
combination of fare, stay and activity. Booking anything, which the gate would stop and
no service here offers. Planning across fields, since a plan is the travel scope's.
Progress reaching the page mid-call, which is the whole page and not this.

## Decisions

**The loop is plugin code, and the model is called only where judgement is.**

- Decompose the request into the day-by-day shape — a `delegate` call, because what to
  do on a Tuesday is not arithmetic.
- Search, score and check — plain Python, because whether €870 exceeds €800 is not a
  thing to ask a model.
- Revise — a `delegate` call for a narrower shape, then search again, bounded to two
  passes.
- Rejected: the turn's own round loop driving four small tools — that is what cora does
  today, and the model deciding it is finished is the reason no plan is checked.

**Giving the checks to code is what makes the loop a loop.**

- A loop can only retry if it can tell that it failed, and a model asked whether it
  succeeded says yes.
- So the terminal condition is a check passing or the passes running out, never the
  model's satisfaction.

**One rule per function, and a violation is a sentence.**

- `check(plan, forecast)` answers with every rule that failed, so a near-miss can be
  offered with all of them named rather than the first.
- A rule the traveller did not state is not a rule: an absent budget is not a budget
  of zero.

**The searches are called directly, not offered to the loop as tools.**

- `Search.flights` fans across departures already, and pairing each with its own stay is
  the joint search the model was doing in prose.
- Nothing goes through `delegate` to reach a price, so the `asks` cards those tools carry
  stay for the model's own calls, where a person is watching.

**The plan is held, not narrated.**

- A frozen shape with a schema, kept under the conversation, so a revision starts from
  what was verified rather than from what the transcript still says.

**Saving passes the plan, and the tool refuses one it did not verify.**

- The gate words its card from the tool's description and the call's arguments and
  nothing else, so a plan that is not an argument is a plan nobody saw before approving.
- So the save takes the plan, and its `run` compares what arrived against the kept one
  and refuses a mismatch.
- The card therefore describes what will be written, and a model that rewrote the middle
  is caught by the comparison rather than trusted.
- Rejected: a title alone, reading the plan out of what was kept — the write would be
  right and the approval blind, which is worse than the card cora ships today.

## Risks / Trade-offs

- One call is thirty to sixty seconds of silence, since a step reaches the reader only
  when the call returns.
- Scoring on total cost is a choice, and a traveller who wanted the shortest flight is
  offered the cheapest one.
- Two revision passes is a guess at where returns stop, and the trace is what makes a
  wrong guess visible.
- A plan is only as fresh as the prices behind it, which the answer says as the searches
  already do.

## Ports, guards and diagrams

- No port changes, no core module touched: this is a plugin, which is the claim being
  made.
- Stands on `Host.state` and `Host.show`, so it merges after both.
- No diagram is regenerated — the component map draws cora, and this adds no adapter.
