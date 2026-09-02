Every item is one failing test, and the list is what shipped rather than what was first
guessed at: eight items came off it during the work, each because the test it asked for
protected nothing a test already here protects. Those are recorded under the group they
left, because a dropped item is a decision and not an absence.

The `README.md` paragraph and the how-to's page are not items: prose is held by a person
reading it. The guards are items, because a guard is a test.

## 1. The outer test

- [x] 1.1 **Outer.** A turn in the travel field calling a stubbed forecast service, the
      model reading what came back labelled untrusted, the trace naming the call and its
      result, and the answer resting on it while citing nothing —
      `tests/acceptance/test_live_sources.py::test_a_question_needing_the_outside_world_is_answered_from_it`.
      The network is stubbed where the client is built, which is the one place it is
      reached: the plugin, its registration and the whole turn are the real ones

## 2. A tool declares what its result is

- [x] 2.1 A declaring tool's result reaching the model behind the untrusted-data label
- [x] 2.2 A tool registered without the declaration reaching the model unlabelled, which
      is the boundary that stops the rule above from being "label everything"
- Dropped: the declaration travelling through the registry — plumbing, and the outer
  test drives it through a real host on the way to the label
- Dropped: two calls of one tool both labelled — the declaration is a field on the tool,
  so there is no per-call path for it to take
- Dropped: a handler unable to take the label off a fetched result — the label is now set
  in one line covering both sources, and the document case already pins that line
- Dropped: the label's wording naming a service — prompt prose, held by a reader

## 3. The guards widen

- [x] 3.1 An extension allowed a technology by name only where its own manifest declares
      the distribution — asked of the plugins and the frontends over one map, replacing
      the frontends-only rule
- [x] 3.2 A plugin importing the technology its neighbour was allowed failing, named with
      what it reached for
- [x] 3.3 Every extension declaring what it reaches for, one added without an entry
      inheriting nothing
- [x] 3.4 A plugin's declared requirements being the app plus what its own allowance names

## 4. The travel scope fetches a forecast

- [x] 4.1 The place resolved, its coordinates forecast, and the answer written as one
      line — the place, the dates, and a high, a low and a word per day
- [x] 4.2 Dates nobody asked for left off the request, so the service answers with its
      own next few days rather than a span beginning nowhere
- [x] 4.3 A place the service resolves to nothing refused in one line naming it, with no
      forecast invented
- [x] 4.4 A service that does not answer refused in one friendly line — unreachable,
      timed out, and answering with a status, which are two doors into one sentence
- [x] 4.5 An answer the tool cannot read refused rather than passed on: unparseable, not
      an object, no days, missing measures, and a shape it does not recognise
- [x] 4.6 The tool offered in the travel field and in no other, declared as returning
      material cora did not write
- [x] 4.7 The real service answering a forecast for a place it knows, marked `integration`
- Dropped: the failed call shown on the trace as that call's — every `ToolRefusal` is
  already reported that way, and the runtime's own suite pins it
- Dropped: a mixed turn citing the passage and not the service — the outer test asserts
  a fetch hands out no citation, and nothing about citing a document moved

## 5. The outer test passes

- [x] 5.1 The outer test passes. It carried no `xfail` marker to drop: it was written
      after the pieces under it rather than before them, which is the one place this
      change departed from the double loop
