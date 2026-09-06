## 1. The outer test

- [x] 1.1 Write the functional test that asks for three days somewhere in a month under a budget and gets a dated plan with a priced fare, a priced stay and a total inside the budget, marked `@pytest.mark.xfail(strict=True)`.

## 2. The plan

- [x] 2.1 Write a test that a plan carries its dates, its days, its fare, its stay and its total.
- [x] 2.2 Write a test that a plan round-trips through its schema unchanged.
- [x] 2.3 Write a test that a plan with no fare and no stay is a plan, and says it is unpriced.

## 3. The checks

- [x] 3.1 Write a test that a stay not covering every night fails, naming that rule.
- [x] 3.2 Write a test that a check-out before the return date fails, naming that rule.
- [x] 3.3 Write a test that a total over the budget fails, and the sentence says by how much.
- [x] 3.4 Write a test that a date in the range with nothing to do fails.
- [x] 3.5 Write a test that nights planned not matching nights asked for fails.
- [x] 3.6 Write a test that an outdoor day the forecast rules out fails.
- [x] 3.7 Write a test that a plan failing three rules comes back with all three.
- [x] 3.8 Write a test that an absent budget is not a budget of zero.
- [x] 3.9 Write a test that a plan satisfying every stated rule comes back with nothing failed.

## 4. The search and the score

- [x] 4.1 Write a test that several candidate departures are priced, each paired with a stay for its own dates.
- [x] 4.2 Write a test that candidates are ordered by total cost, fare and stay together.
- [x] 4.3 Write a test that the cheapest candidate passing its checks is the one chosen.
- [x] 4.4 Write a test that a cheaper candidate failing a check is passed over rather than fixed up.
- [x] 4.5 Write a test that a departure the service refused does not lose the departures that worked.

## 5. The loop

- [x] 5.1 Write a test that the day-by-day shape comes from one delegated call, given the request and the documents.
- [x] 5.2 Write a test that a first pass failing its checks is followed by a revision and a second search.
- [x] 5.3 Write a test that the loop stops as soon as a candidate passes.
- [x] 5.4 Write a test that the loop stops after two revisions and offers the closest plan it reached.
- [x] 5.5 Write a test that a plan offered after the passes run out names every check it failed.
- [x] 5.6 Write a test that no constraint the traveller gave is relaxed to make a plan pass.
- [x] 5.7 Write a test that a model claiming success does not end the loop when a check still fails.

## 6. Keeping and revising

- [x] 6.1 Write a test that a planned trip is kept for the conversation it was planned in.
- [x] 6.2 Write a test that asking for it cheaper re-searches the kept trip under a lower ceiling.
- [x] 6.3 Write a test that a revision is checked again before it is offered.
- [x] 6.4 Write a test that a revision nothing can satisfy leaves the kept plan standing and says which part failed.
- [x] 6.5 Write a test that a second conversation planning a trip does not see the first one's plan.

## 7. The trace

- [x] 7.1 Write a test that the candidates priced stand under the planning call.
- [x] 7.2 Write a test that each failed check is shown, naming the rule.
- [x] 7.3 Write a test that each revision is shown, and a reader can count them.

## 8. Saving what was verified

- [x] 8.1 Write a test that the save writes the plan that passed its checks.
- [x] 8.2 Write a test that the card carries that plan's dates, fare, stay and total as the call's arguments.
- [x] 8.3 Write a test that a call whose plan differs from the kept one is refused and writes nothing.
- [x] 8.4 Write a test that the save still waits for approval, and a decline writes nothing.
- [x] 8.5 Write a test that a save with no plan kept refuses in a sentence rather than writing an empty file.

## 9. No key, and a failing service

- [x] 9.1 Write a test that the planner is registered with no search key set.
- [x] 9.2 Write a test that with no key it plans the days, checks what it can, and says the trip is unpriced.
- [x] 9.3 Write a test that a service that cannot be reached costs the plan its prices and not the turn.

## 10. Reach and labelling

- [x] 10.1 Write a test that both planning tools are offered in the travel scope only.
- [x] 10.2 Write a test that what the planner returns reaches the model under the untrusted label.

## 11. Close it

- [x] 11.1 Drop the outer test's `xfail` marker and watch it pass.
