## Why

Cora describes a trip in prose it never checks, so a plan can be over budget or booked
past the flight home and read perfectly well.

## What Changes

- One instruction plans a whole trip: the days, the fare, the stay, and what it costs
- The travel plugin runs the planning loop itself, and the loop decides when it is done
- A plan is a shape the plugin holds, not a paragraph the model wrote
- Candidate weeks are priced for real and scored, so the plan is searched rather than guessed
- Every plan is checked — dates, nights, budget, empty days, weather — before it is offered
- A plan that fails a check is revised and searched again, twice, then handed over as it is
- What it could not solve is named plainly, and no constraint is ever quietly relaxed
- The plan is kept for the conversation, so a change revises it rather than replanning
- The planning shows on the trace: what it searched, what it scored, what it fixed
- Saving an itinerary writes the plan that was verified, rather than prose about it
- Without a search key it plans and checks everything but the money, and says so
- New capability `plans`, which says what a planned trip is and what it promises

## Impact

- `plugins/travel/.../plan.py` — new: what a plan is, and the schema it travels as
- `plugins/travel/.../constraints.py` — new: what a plan must satisfy, one rule per function
- `plugins/travel/.../planner.py` — new: the loop, and the two tools that enter it
- `plugins/travel/.../trips.py` — the searches called directly as well as offered to the model
- `plugins/travel/.../itinerary.py` — **BREAKING** takes a structured plan, and refuses an unverified one
- `plugins/travel/.../__init__.py` — two more tools, and instructions that name the planner
- `README.md`, `docs/how-to/write-a-plugin.md` — the plugin that plans, as the worked example
- Depends on: `a-plugin-remembers-across-turns` for the plan, `a-plugin-shows-its-work` for the trace
- Left alone: the gate, which still stops the save and is still cora's own
- Left alone: the researcher, the forecast, and both searches as the model already calls them
- Left alone: every core module, which this change does not touch
