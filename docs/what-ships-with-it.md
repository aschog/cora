# What ships with it

Three plugins, and everything here is theirs rather than cora's. A deployment with none
of them still answers.

- **security** — a medical filter and a prompt-injection screen, both system-wide.
- **fitness** — a coaching persona and its calculators, bringing the `fitness` field.
- **travel** — the `travel` field, and the rest of this page.

## Travel, in four parts

**Its own notes.** Under `plugins/travel/src/cora/plugins/travel/corpus/` — upload them
in the rail with `travel` picked.

**It digs.** Ask what to do with three days somewhere and a researcher runs a bounded
loop of its own, one lookup at a time, and reports once: the conversation carries the
answer, the trace carries the searching. Out of rounds, it writes up what it has and
says so.

**It reaches past its documents.** Ask what the weather will do and it calls a live
forecast — no key needed. What a service says reaches the model behind the same
untrusted-data label a passage carries, and earns no `[n]`, because a citation opens
onto a file you uploaded and a forecast is not one. A service that is down costs that
call, not the turn.

**It plans.** Ask for three days in a month under a budget and it asks the model what to
do on each day, prices every week the window allows, pairs the cheapest with a stay, then
*checks* what it built: the stay covers every night, the nights match what was asked, the
total is inside the budget, no day is empty, and no outdoor day sits under a forecast that
rules it out. A plan that fails is revised twice, then handed over naming every rule it
could not satisfy — nothing is quietly relaxed. The plan is a shape cora keeps, so *make
it cheaper* revises what was verified.

**It saves, once you say so.** `save_itinerary` declares that it changes something
outside cora, so asking travel to save the trip stops the turn: you see the call, and
only then does a file land under `cora-output`. It writes the plan that passed — handed
anything else, it refuses, saying that is not the trip it checked.

## Prices, and the one key cora needs

Give it a route, a budget and a month rather than a fixed date, and it returns the three
cheapest fares and the three cheapest stays, priced and dated.

- Named without a where-from or a when, it stops and asks: a card of the search's own
  fields. Nothing reaches the service until you submit it.
- A window is a search, not a lookup: one candidate a week across the range, widening
  the interval rather than searching less when the range is long.
- Your budget and restrictions go *into* the search, so an option you ruled out is one
  you never see.
- Set `CORA_PLUGIN_TRAVEL_SERPAPI_KEY` and the two searches appear; set nothing and they
  are never offered. Prices are what the aggregator showed, not a seat held for you.

Or drive them with no account and no network — the fake service makes its prices out of
the dates it is asked about, so a window really has a cheapest week in it:

```sh
uv run python scripts/fake_search_service.py    # in its own terminal
export CORA_PLUGIN_TRAVEL_SERPAPI_KEY=anything
export CORA_PLUGIN_TRAVEL_SEARCH_URL=http://127.0.0.1:8909/search
```

Nothing in the plugin branches on that URL, so what you drive is the code that ships.
