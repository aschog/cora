Every item is one failing test. Group 2 comes first because the researcher has nothing to
be withheld from until an effect can be declared, and group 3 before group 4 because a
ceiling that loses its findings is what the researcher would report.

The how-to's page and `README.md` are not items: prose is held by a person reading it. The
guards are items, because a guard is a test.

## 1. The outer test

- [ ] 1.1 **Outer.** Write a test that shows a turn in the travel field calling the
      researcher, the loop making several lookups against a stubbed service and the
      documents, the turn's model told one report rather than each lookup, and the
      lookups on the trace nested under the call that started them —
      `tests/acceptance/test_researcher.py::test_a_broad_question_is_researched_not_answered_in_one_pass`,
      marked `@pytest.mark.xfail(strict=True)`

## 2. A tool says whether it changes anything outside cora

- [ ] 2.1 Write a test that shows a tool registered with the declaration carrying it
      through the registry to where a call is run
- [ ] 2.2 Write a test that shows a tool registered without it read as changing nothing
- [ ] 2.3 Write a test that shows the listing marking a tool that declares an effect, and
      not its neighbours

## 3. A sub-agent reads and does not act

- [ ] 3.1 Write a test that shows a tool declaring an effect absent from what a delegated
      loop is offered, though it was passed in
- [ ] 3.2 Write a test that shows the plugin's own logger naming the tool that was withheld
- [ ] 3.3 Write a test that shows a tool declaring nothing still offered, so the filter
      withholds one thing and not everything
- [ ] 3.4 **Guard.** Write a test that shows what a delegated loop is offered holding
      nothing that writes, nothing that stops the turn and nothing that declares an
      effect — asked of the host with all three passed in

## 4. A ceiling reports instead of losing what it found

- [ ] 4.1 Write a test that shows a loop spending its allowance without answering coming
      back with what it found rather than raising
- [ ] 4.2 Write a test that shows that report saying it stopped early
- [ ] 4.3 Write a test that shows the close-out call offered no tools, so it cannot dig
      further
- [ ] 4.4 Write a test that shows a loop stopped having found nothing saying that, with
      nothing presented as a finding
- [ ] 4.5 Write a test that shows a close-out that comes back empty falling back to the
      refusal rather than reporting nothing as something
- [ ] 4.6 Write a test that shows a loop that answers within its allowance unaffected,
      carrying no caveat
- [ ] 4.7 Write a test that shows the host's allowance still bounding a loop that asked
      for more, at any depth

## 5. The travel scope ships a researcher

- [ ] 5.1 Write a test that shows the researcher registered under the travel scope and in
      no other, alongside the forecast tool
- [ ] 5.2 Write a test that shows it passing the forecast tool to the loop, so a lookup
      about weather can be made
- [ ] 5.3 Write a test that shows its rounds read from the plugin's own settings
- [ ] 5.4 Write a test that shows a deployment naming no rounds getting the plugin's own
      default
- [ ] 5.5 Write a test that shows a rounds setting that is not a number refused at load,
      naming the plugin
- [ ] 5.6 Write a test that shows what the researcher answered reaching the turn labelled
      untrusted, the documents having gone into it

## 6. Nothing under `src/cora/` was needed for the researcher itself

- [ ] 6.1 Write a test that shows the travel plugin naming the contract alone — no part of
      the engine, and no technology beyond what its own manifest buys

## 7. The outer test passes

- [ ] 7.1 Drop the `xfail` marker from 1.1 and watch the outer test pass
