## 1. The outer test

- [ ] 1.1 Write the functional test that asks for three days somewhere in a month under a budget and gets a dated plan with a priced fare, a priced stay and a total inside the budget, marked `@pytest.mark.xfail(strict=True)`.

## 2. The plan

- [ ] 2.1 Write a test that a plan carries its dates, its days, its fare, its stay and its total.
- [ ] 2.2 Write a test that a plan round-trips through its schema unchanged.
- [ ] 2.3 Write a test that a plan with no fare and no stay is a plan, and says it is unpriced.

## 3. The checks

- [ ] 3.1 Write a test that a stay not covering every night fails, naming that rule.
- [ ] 3.2 Write a test that a check-out before the return date fails, naming that rule.
- [ ] 3.3 Write a test that a total over the budget fails, and the sentence says by how much.
- [ ] 3.4 Write a test that a date in the range with nothing to do fails.
- [ ] 3.5 Write a test that nights planned not matching nights asked for fails.
- [ ] 3.6 Write a test that an outdoor day the forecast rules out fails.
- [ ] 3.7 Write a test that a plan failing three rules comes back with all three.
- [ ] 3.8 Write a test that an absent budget is not a budget of zero.
- [ ] 3.9 Write a test that a plan satisfying every stated rule comes back with nothing failed.

## 4. The search and the score

- [ ] 4.1 Write a test that several candidate departures are priced, each paired with a stay for its own dates.
- [ ] 4.2 Write a test that candidates are ordered by total cost, fare and stay together.
- [ ] 4.3 Write a test that the cheapest candidate passing its checks is the one chosen.
- [ ] 4.4 Write a test that a cheaper candidate failing a check is passed over rather than fixed up.
- [ ] 4.5 Write a test that a departure the service refused does not lose the departures that worked.

## 5. The loop

- [ ] 5.1 Write a test that the day-by-day shape comes from one delegated call, given the request and the documents.
- [ ] 5.2 Write a test that a first pass failing its checks is followed by a revision and a second search.
- [ ] 5.3 Write a test that the loop stops as soon as a candidate passes.
- [ ] 5.4 Write a test that the loop stops after two revisions and offers the closest plan it reached.
- [ ] 5.5 Write a test that a plan offered after the passes run out names every check it failed.
- [ ] 5.6 Write a test that no constraint the traveller gave is relaxed to make a plan pass.
- [ ] 5.7 Write a test that a model claiming success does not end the loop when a check still fails.

## 6. Keeping and revising

- [ ] 6.1 Write a test that a planned trip is kept for the conversation it was planned in.
- [ ] 6.2 Write a test that asking for it cheaper re-searches the kept trip under a lower ceiling.
- [ ] 6.3 Write a test that a revision is checked again before it is offered.
- [ ] 6.4 Write a test that a revision nothing can satisfy leaves the kept plan standing and says which part failed.
- [ ] 6.5 Write a test that a second conversation planning a trip does not see the first one's plan.

## 7. The trace

- [ ] 7.1 Write a test that the candidates priced stand under the planning call.
- [ ] 7.2 Write a test that each failed check is shown, naming the rule.
- [ ] 7.3 Write a test that each revision is shown, and a reader can count them.

## 8. Saving what was verified

- [ ] 8.1 Write a test that the save writes the kept plan rather than an argument the model wrote.
- [ ] 8.2 Write a test that the card put to the traveller describes that plan's dates, fare, stay and total.
- [ ] 8.3 Write a test that the save still waits for approval, and a decline writes nothing.
- [ ] 8.4 Write a test that a save with no plan kept refuses in a sentence rather than writing an empty file.

## 9. No key, and a failing service

- [ ] 9.1 Write a test that the planner is registered with no search key set.
- [ ] 9.2 Write a test that with no key it plans the days, checks what it can, and says the trip is unpriced.
- [ ] 9.3 Write a test that a service that cannot be reached costs the plan its prices and not the turn.

## 10. Reach and labelling

- [ ] 10.1 Write a test that both planning tools are offered in the travel scope only.
- [ ] 10.2 Write a test that what the planner returns reaches the model under the untrusted label.

## 11. Close it

- [ ] 11.1 Drop the outer test's `xfail` marker and watch it pass.
