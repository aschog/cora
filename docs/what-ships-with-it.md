# What ships with it

cora loads no plugin unless it is named, so a bare cora is the whole of it: it searches
its documents, remembers what it is told, asks when it cannot tell, and cites what it
used. This repository ships three plugins beyond that, and everything below is theirs
rather than cora's — a deployment that names none of them has none of it.

The medical filter and the prompt-injection screen are `cora.plugins.security`, and they
are system-wide: they hold whatever a turn is running as. The coaching persona and its
calculators are `cora.plugins.fitness`, which brings the `fitness` field. The rest of
this page is `cora.plugins.travel`, which brings `travel` — and which is the plugin this
repository uses to show what the contract can carry.

## Notes to answer from

The travel plugin ships its notes as files under
`plugins/travel/src/cora/plugins/travel/corpus/`; upload them in the documents rail,
with `travel` picked as the field, to give it something to answer from.

## It digs

It also digs. Ask it what to do with three days somewhere and it sends a researcher: a
tool that runs a bounded loop of its own, makes its lookups one at a time, and comes back
with a single report — so the conversation carries the answer while the trace carries the
searching, nested under the call that started it. Run out of rounds and it writes up what
it has and says so, rather than losing it or offering it as the whole story.

## It reaches past its documents

It also reaches past its documents. Ask it what the weather will do and it calls a live
forecast service — no key, nothing to configure — and answers from what came back. A
document holds what somebody wrote down once, and this is the part of an answer that has
to be current instead. What a service says is not cora's own words, so it reaches the
model behind the same untrusted-data label a passage carries, and no plugin can take
that off.
It earns no `[n]`: a citation opens onto a passage of a file you uploaded, and a
forecast has none, so the answer says it in cora's own prose and the trace is the record
of the call. A service that is down costs the turn that one call — a friendly sentence,
and the conversation intact.

## It plans, and checks what it planned

And it plans, rather than describing a plan. Ask for three days somewhere in a month
under a budget and it works out the steps itself: it asks the model what to do on each
day, prices every week the window allows, pairs the cheapest few with a place to stay
for their own dates, and then *checks* what it built — the stay covers every night, the
return matches the check-out, the total is inside the budget, no date is empty, no
outdoor day sits under a forecast that rules it out. A plan that fails a check is
revised and searched again, twice, and then handed over with every rule it could not
satisfy named. Nothing is quietly relaxed: a budget it cannot meet is said plainly, not
raised. The plan is a shape cora holds rather than a paragraph, kept for the
conversation, so *make it cheaper* revises what was verified instead of starting again —
and saving it writes the plan that passed, refusing one that does not match.

## It prices what it planned

It also prices what it plans piece by piece. Give it a route, a budget and a month you
might go rather than a date you have fixed, and it comes back with the three cheapest
fares and the three cheapest places to stay, each priced and dated. Name a trip without
saying where from or when, and it stops and asks you: a card of the search's own
fields, dates as date pickers, and a button that stays shut until the trip is filled
in. Nothing
reaches the service until you submit it, and what is priced is what you wrote.

A window is a search rather than a lookup — the service wants a departure date, so cora
tries one candidate a week across the range and keeps the best of all of them, widening
the interval rather than quietly searching less when the range is long. Your budget and
your restrictions go *into* the search, so an option you ruled out is one you never see
rather than one shown with a caveat. This is the one thing in cora that needs a key: set
`CORA_PLUGIN_TRAVEL_SERPAPI_KEY` and the two searches appear, set nothing and they are
never offered — a tool that can only fail is worse than a tool that was never there.
Prices are what the aggregator showed, not a seat held for you, and the answer says so.

You can drive all of that with no account and no network.
`scripts/fake_search_service.py` answers in the same two shapes and makes its prices out
of the dates it is asked about, so a window really does have a cheapest week in it:

```sh
uv run python scripts/fake_search_service.py    # in its own terminal
export CORA_PLUGIN_TRAVEL_SERPAPI_KEY=anything
export CORA_PLUGIN_TRAVEL_SEARCH_URL=http://127.0.0.1:8909/search
```

`CORA_PLUGIN_TRAVEL_SEARCH_URL` is where the searches go, and the real service is where
they go unless you say otherwise — nothing in the plugin branches on it, so what you are
driving is the code that ships.
