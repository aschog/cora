Every item is one failing test. The docs this change touches carry no items: a `.md` file
is prose, and prose is held by a person reading it — except a claim a guard can read,
which is why the output location has one.

## 1. The outer test

- [x] 1.1 **Outer.** A turn in the travel field whose model asks to save an itinerary,
      the turn stopping with what the call would do, no file existing until it is
      approved, and the trace holding the approval beside the call —
      `tests/acceptance/test_effects.py::test_an_effect_happens_only_after_i_approve_it`,
      marked `@pytest.mark.xfail(strict=True)`

## 2. An approval is bound to the call it answers

- [x] 2.1 A proposal carrying the call's id, the tool, what it says it does, and the
      arguments as the model wrote them — held by 3.5's test, which is the one place
      either shape does anything
- [x] 2.2 An approval carrying that same call id and a yes or no, so two in one round are
      told apart — the same test: `approves` is where the binding is a behaviour
- [x] 2.3 A parked turn carrying a proposal where it stopped on one, and a decision where
      it stopped on that
- [x] 2.4 A parked turn claiming both, or neither, refused as the shape it cannot be

## 3. An effect stops the round it was proposed in

- [ ] 3.1 A round asking for a tool that declares an effect stopping before that tool runs
- [ ] 3.2 A round asking only for tools that declare none never stopping
- [ ] 3.3 An approved call running, and the trace holding the approval and the call it
      authorised
- [ ] 3.4 A declined call not running, the model told it was declined, and the turn still
      answered
- [ ] 3.5 An answer that is not an approval of the call proposed read as a decline
- [ ] 3.6 The default pause declining, so a caller that cannot ask changes nothing
- [ ] 3.7 A proposed call naming no registered tool passing the gate untouched, and being
      refused where a call always was

## 4. Two effects in one turn, and nothing runs twice

- [ ] 4.1 A round proposing two effects stopping twice, each proposal naming its own call
- [ ] 4.2 Both approved, and each tool call running exactly once
- [ ] 4.3 One approved and one declined, only the approved one running and the model told
      about both
- [ ] 4.4 Neither tool having run at the moment the second proposal is put, which is what
      settling ahead of the round means

## 5. The gate is cora's, and no call goes round it

- [ ] 5.1 **Guard.** The walk the runner wires reaching the tools through the gate and
      through nothing else
- [ ] 5.2 A plugin subscribed to every point it may, and the gate still stopping its own
      effecting tool
- [ ] 5.3 The recursion limit sized for the gate, the round budget still tripping first,
      measured as the existing sizing test measures it
- [ ] 5.4 The committed round sequence redrawn from the walk the runner now wires

## 6. What an effect produces is a file the user keeps

- [x] 6.1 A write through the output port landing as a file under the root, answering
      with where it landed
- [x] 6.2 A name that climbs out of the root refused, and nothing written outside it
- [x] 6.3 The location read from the environment, and the default used where nothing
      names one
- [x] 6.4 A plugin handed the output location through the host rather than a path of its
      own
- [x] 6.5 The committed component map redrawn for the new port and its adapter
- [x] 6.6 The docs guard finding the output location `README.md` claims

## 7. The travel scope can save an itinerary

- [x] 7.1 The itinerary tool registered under the travel scope, declaring its effect, and
      under no other scope
- [x] 7.2 The listing showing it as having an effect, and its neighbours as having none —
      already held by `test_plugin_set.py` and `test_listing.py`, over the note the
      registry writes; the travel half is 7.1's assertion
- [x] 7.3 The tool writing what it was given through the host's output, and answering
      with where the file is
- [x] 7.4 The travel instructions naming the tool, so the model offers to save rather
      than saving unasked

## 8. The page shows what cora is about to do

- [ ] 8.1 The pending endpoint answering with a proposal where the turn stopped on one,
      and a decision where it stopped on that
- [ ] 8.2 The endpoint that answers a proposal, approving and declining, and refusing one
      for a thread waiting on nothing
- [ ] 8.3 A streamed turn reporting a proposal as the paused event the page reads
- [ ] 8.4 The card drawing what the call would do and its arguments, with an approve and
      a decline
- [ ] 8.5 The card reading as settled once answered, saying which way it went
- [ ] 8.6 A page reopened while a turn is stopped finding the proposal and drawing it

## 9. The outer test passes

- [ ] 9.1 The `xfail` marker dropped, and the outer test passing
