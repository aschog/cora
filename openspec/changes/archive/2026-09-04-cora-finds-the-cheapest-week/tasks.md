## 1. The outer test

- [x] 1.1 Write the functional test that asks for a week somewhere in a two-month range under a budget and gets three priced flights and three priced stays, marked `@pytest.mark.xfail(strict=True)`.

## 2. The flight search

- [x] 2.1 Write a test that a search for a route and two fixed dates returns the options the service answered with.
- [x] 2.2 Write a test that it returns at most three of them, cheapest first.
- [x] 2.3 Write a test that each option carries its price, its currency and its dates.
- [x] 2.4 Write a test that a service answering with no option is one sentence saying so.

## 3. A window instead of two dates

- [x] 3.1 Write a test that a month range and a trip length are searched as several departures, one call each.
- [x] 3.2 Write a test that the cheapest three across all of those departures come back, each naming its own dates.
- [x] 3.3 Write a test that the default stride is weekly, and that a closer stride is honoured when asked for.
- [x] 3.4 Write a test that a stride that would exceed the candidate cap is widened, and that the answer says how many departures were tried.
- [x] 3.5 Write a test that two fixed dates fire exactly one call.

## 4. The accommodation search

- [x] 4.1 Write a test that a place, a check-in and a check-out return at most three stays, cheapest first, each priced for the stay.
- [x] 4.2 Write a test that it fires one call and never fans out across the window.

## 5. Restrictions the service holds

- [x] 5.1 Write a test that a stated price ceiling reaches the service as its own parameter.
- [x] 5.2 Write a test that a kind of place ruled out reaches the service as its own parameter.
- [x] 5.3 Write a test that nothing is filtered after the answer comes back, so an option returned is an option shown.
- [x] 5.4 Write a test that every searchable field reaches the model's schema and the outgoing query from the one table that declares it.
- [x] 5.5 Write a test that a field needing shaping is written the way its row says, not passed through.
- [x] 5.6 Write a test that a field the traveller did not state is left out of the query rather than sent empty.

## 6. A failing service

- [x] 6.1 Write a test that an unreachable service is one sentence and the turn is otherwise intact.
- [x] 6.2 Write a test that an answer this cannot read is a different sentence, not an exception.
- [x] 6.3 Write a test that a route the service does not know is a sentence naming what to try instead.
- [x] 6.4 Write a test that one failed departure among several does not lose the departures that worked.

## 7. The credential

- [x] 7.1 Write a test that neither tool is registered when no key is set for the plugin.
- [x] 7.2 Write a test that both are registered when one is, and that the rest of the scope is unchanged either way.
- [x] 7.3 Write a test that the key appears in neither the trace nor what the model is given.

## 8. Reach and labelling

- [x] 8.1 Write a test that both tools are offered in the travel scope only.
- [x] 8.2 Write a test that what each returns reaches the model under the untrusted label and earns no citation.

## 9. Close it

- [x] 9.1 Drop the outer test's `xfail` marker and watch it pass.
