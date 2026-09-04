## Context

The travel scope already reaches one live service, so the shape of a fetching tool is
settled and this change follows it. See proposal.md — Why.

## Goals / Non-Goals

**Goals:**

- Two searches that answer in prices, under the tool shape the forecast already proved.
- A window the traveller has not fixed, searched without the model driving the search.
- A restriction held by the service's own parameters rather than by cora's prose.
- A credential that a deployment may not have, costing that deployment nothing.
- A search field nobody has asked for yet arriving as one line rather than three.

**Non-Goals:**

- Booking anything, or carrying the service's affiliate link into the answer.
- Converting between currencies, which invents a rate the service did not give.
- Searching accommodation across the window too, which multiplies calls by candidates.
- Caching a result between turns, which is a store this plugin does not have.
- A unit of work, a repository or a store, none of which a read with no state needs.

## Decisions

- **SerpApi's Google Flights and Google Hotels engines** — Amadeus retired its
  self-service portal in July 2026, Booking.com's Demand API is partner-gated and its
  terms forbid an AI system without written approval, and Duffel's free tier answers
  with invented prices. What is left with a self-signup and real numbers is the search
  proxy over what Google already aggregates.
- **Two tools, not one trip search** — the cheapest flight and the cheapest hotel are
  found by different queries and pair arbitrarily, so pairing them belongs in the
  answer's prose where the traveller can argue with it.
- **The fan-out is code inside the flight tool, not a loop the model drives** — the
  engine requires an outbound date, so a window means one call per candidate departure,
  and nine model rounds would cost tokens and a shallow trace where one call reads
  clearly.
- **Candidates are capped, and the stride widens rather than the range silently
  shrinking** — a daily stride over two months is fifty-four calls against an hourly
  limit, so the tool widens the interval to fit the cap and says in its answer how many
  departures it actually tried.
- **The calls go out through a stdlib thread pool over the one client** — sequential is
  half a minute of a turn hanging, and the pool is three lines against a client that is
  already safe to share.
- **Registration is conditional on the key, as saving is on an output** — a tool the
  model can call and that can only fail is worse than one it is never offered, which is
  the rule this plugin already follows.
- **Airport codes come from the model** — the engine wants a code, a model knows them,
  and a resolution endpoint is a second call to buy something already had.
- **A restriction exists only where the service has a parameter for it** — a filter cora
  applies after the fact is a filter the traveller cannot trust, so the schema offers a
  price ceiling, a star rating, a stop count and the kinds of place to exclude, and
  nothing that would have to be honoured in prose.
- **Of the layered architecture, only the service and its value survive** — the tool
  function is the service, a frozen record is what it takes, and the seam onto the
  network is the protocol the forecast already defines; a unit of work guards a
  transaction that does not exist here, and a repository loads from a store this plugin
  does not have.
- **The searchable fields are one declarative table, read twice** — the parameter schema
  the model is shown and the query the service is sent are both built from it, so a
  field the traveller wants later is a row rather than an edit in three places, and a
  field that needs shaping carries its own way of writing itself.
- **Every failure is a `ToolRefusal` carrying one sentence** — unreachable, unreadable,
  a route the service does not know, and a search that returned nothing are four
  sentences the turn answers around, exactly as the forecast's are.

## Risks / Trade-offs

- The free tier is 250 searches a month and 50 an hour, and one flexible window spends
  about nine → the cap, the weekly default and an answer that states its own cost.
- The service scrapes a page whose shape can move → the same refusal discipline as the
  forecast, so a moved shape is one sentence rather than a broken turn.
- Prices are what the aggregator showed, not a seat held → the scope's instructions say
  so, beside the line that already says a document's fare is not today's.
- A destination and a date range now leave the machine to a third party → the privacy
  page names the host, and the reader is told what the query carries.
- A traveller's budget spans flight plus stay, but each search holds only its own
  ceiling → the model states the total, and the ceilings stay per search rather than
  becoming a bundle cora would have to split.

## Migration Plan

Nothing stored changes, so a deployment without the key is the current behaviour
unchanged. Removing the key removes the two tools and nothing else.

## Ports, guards and diagrams

No port changes, no core changes, and no diagram is redrawn — the plugin's manifest
already buys the one technology this needs, so the packaging guard is untouched.
