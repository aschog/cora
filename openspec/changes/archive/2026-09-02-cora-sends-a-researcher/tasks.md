Every item is one failing test, and the list is what shipped rather than what was first
guessed at: eight items came off it during the work, each because the test it asked for
protected nothing already protected here. Those are recorded under the group they left,
because a dropped item is a decision and not an absence.

One existing test was **rewritten rather than kept**: `test_plugin_host.py` pinned the
old outcome at the ceiling — a failed call — and this change's delta spec modifies that
requirement. The spec moved, so the test moved with it.

Review then added four items and rewrote two. Its findings are folded in below rather
than listed apart, because a list that records what was planned and not what shipped is
the wrong document to read next sprint.

## 1. The outer test

- [x] 1.1 **Outer.** A turn in the travel field calling the researcher, the loop making
      two lookups against a stubbed service and the documents, the turn's model told one
      report rather than each lookup, and the lookups on the trace nested under the call
      that started them —
      `tests/acceptance/test_researcher.py::test_a_broad_question_is_researched_not_answered_in_one_pass`.
      Written first this time, and red until group 5 landed

## 2. A tool says whether it changes anything outside cora

- [x] 2.1 A plugin registering a tool with the declaration through the contract, the
      registration carrying it — the only thing proving the keyword, which is why the
      item planned for dropping stayed
- [x] 2.2 The listing marking a tool that declares an effect and not its neighbours,
      carried as a note so both renderings and a fifth kind read one shape
- [x] 2.3 The terminal rendering showing that note on its own line
- [x] 2.4 The page's plug menu showing it too, drawn off the note rather than off the kind
- Dropped: a tool registered without the declaration read as changing nothing — the
  offered-set test asserts an exact set, so a filter that withheld everything fails it

## 3. A sub-agent reads and does not act

- [x] 3.1 **Guard.** What a delegated loop is offered holding nothing that writes,
      nothing that stops the turn and nothing that declares an effect — asked of the host
      with a reading tool and an effecting one both passed in, and asserted as an exact
      set, which is what makes it one test instead of three
- [x] 3.2 The plugin's own logger naming the tool that was withheld
- Dropped: an effecting tool absent from the offered set, and a reading one still
  present — both are the exact-set assertion in 3.1, stated once

## 4. A ceiling reports instead of losing what it found

- [x] 4.1 A loop spending its allowance without answering coming back with what it found
      and a heading saying it stopped early, the host's ceiling still bounding the rounds
- [x] 4.2 The close-out call offered no tools, which is what keeps it from digging further
- [x] 4.3 A close-out that says nothing falling back to the refusal, so nothing empty is
      dressed up as a report
- [x] 4.4 A loop that gathered nothing refusing rather than being asked to write up
      nothing — put back by review, and it was the one drop of the eight that hid a real
      defect: the write-up fired on an empty transcript, so every nested call arriving
      after the pot emptied bought a model call the allowance never authorised
- [x] 4.5 Fanning out after the allowance is gone buying no further model calls —
      measured at 12 calls for a fan-out of 10 before the fix, 3 after, and the width is
      the model's choice
- [x] 4.6 The inherited depth guard counting rounds apart from write-ups. It had drifted
      to zero headroom and was passing for a reason it was not written for: two of the
      six calls it counted as "rounds spent" were write-ups
- Dropped: the report saying it stopped early as its own test — it is one assertion in 4.1
- Dropped: a loop answering within its allowance unaffected, and the allowance bounding
  at any depth — both already pinned by the delegation tests this change inherited

## 5. The travel scope ships a researcher

- [x] 5.1 The researcher registered under the travel scope and in no other, beside the
      forecast, both declared as returning material cora did not write and neither an effect
- [x] 5.2 Its loop offered the forecast beside cora's document search
- [x] 5.3 The rounds read from the plugin's own settings, and the default where none is named
- [x] 5.4 A rounds setting that is not a number refused while the plugin registers, and
      the operator told which setting and what they set it to. Review found the first
      version certified a message nobody sees: cora keeps a plugin's exception text out
      of what the operator reads, so the plugin now raises the one error that passes
      through worded
- [x] 5.5 The rounds it asks for being the rounds the loop actually spends. **Rewritten
      after review**, which found the first version asserted a call count that is
      identical for every setting — it would have passed for a researcher ignoring the
      setting entirely. It now reads how the loop *ended*, and a mutation hard-coding
      the default makes it fail
- [x] 5.6 The forecast handed to every loop being one tool, built where the plugin
      registers — one per question would parse the certificate bundle again and reuse no
      connection
- Dropped: what the researcher answered reaching the turn labelled untrusted — inherited
  behaviour, and the delegation tests already pin it

## 6. Nothing under `src/cora/` was needed for the researcher itself

- Dropped: the travel plugin naming the contract alone. The architecture guard already
  asserts it over every plugin file, and a second assertion of the same rule is not a
  second guard. The researcher is 90 lines of plugin over `Host.delegate`; what this
  change did touch in the core is the effect mark and the ceiling, neither of which the
  researcher needed

## 7. The outer test passes

- [x] 7.1 The `xfail` marker dropped, and the outer test passing
