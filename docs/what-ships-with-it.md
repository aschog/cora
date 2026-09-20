# What ships with it

Five plugins, and everything here is theirs rather than cora's. A deployment with none
of them still answers.

- **security** — a medical filter and a prompt-injection screen, both system-wide.
- **fitness** — a coaching persona, its calculators, a trainer to work a session in, and
  the log it wrote, read back as numbers.
- **interview** — the `interview` field: mock interviews run on a card, answers judged
  against a rubric, and a report the user keeps.
- **vocab** — the `vocab` field: the word lists you are learning from, answered from and
  cited like any other document, and drilled from a schedule the plugin keeps.
- **travel** — the `travel` field, and the rest of this page.

## Fitness brings a screen

Pin a conversation to `fitness` and the middle of the page becomes a trainer: the plan
one exercise at a time, its sets and working weight, the clip for it playing in the same frame, and the camera to film yourself against, which takes the whole page while it runs, with the controls drawn over the picture. **Finish** — which reads *no sets logged yet* until one is, *saving* while the save is
out, and *saved* once cora has the workout — writes it into the `fitness` field as a
Markdown document named for the moment it was saved and then for the sheet's tab the
plan came from, opening with that same name — so the next question about it is answered
from your own log, with the day cited. Refused or unreachable, nothing is lost and
nothing is saved twice: the sets stay logged, the strip says why, and **Finish** is
offered again.

The field is the only log. **History** is what cora holds, read back by name, and a
fresh workout opens each exercise on the weight and reps of the last save that worked
it — so a second browser, or a reinstall, starts where the first left off. There is
nothing to export, because there is nothing here to carry.

Ask what you trained and the coach lists the log rather than searching it.
`list_workouts` reads every dated document of the field and answers in text the coach
shows as it is: one line per day naming the workouts trained, in whatever language the
sheet names them, the exercises of a save that carries no name, and a last line saying
how many days and saves it holds. Ask for the details and each movement comes with its load, sets,
reps, volume and a mark where it rose on the last time. It narrows to one lift, or to
the days since one. A search finds the sessions worded like the question, and the
listing finds all of them.

The plan comes from a published Google Sheet, read each time the trainer is opened: one
row per exercise, with its sets, reps, working weight and clips. Edit the sheet and the
next open follows it. Which sheet is named in the page, and that is how you point it at
your own — the page is a file of the plugin, not a setting cora reads, because what is
handed to your browser is the file as it sits on disk.

Out of signal, the trainer keeps working: the plan last read stands, and failing that
the one written into the page — fifteen kettlebell exercises, in the language the coach
answers in. The strip says which of the three you are training from. The sheet, the clips and the pose tracking come from the services they came from, so
those want a network. Everything else it does is local.

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
