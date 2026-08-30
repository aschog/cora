Every item is one failing test, and group 2 comes first because the rest register through
it.

## 1. The outer test

- [x] 1.1 **Outer.** Write a test that shows a fixture plugin registering a tool, an
      instruction and a rule through `extend`, and a turn using all three. Mark it
      `@pytest.mark.xfail(strict=True)`

## 2. The host and what registering means

- [x] 2.1 Write a test that shows a module's `extend` is called with a host when it loads
- [x] 2.2 Write a test that shows a registered tool is offered to the model
- [x] 2.3 Write a test that shows registered instructions reach the brief under the
      plugin's heading
- [x] 2.4 Write a test that shows a registered rule screens what the user types
- [x] 2.5 Write a test that shows every registration carries the module that made it
- [x] 2.6 Write a test that shows a module registering nothing loads and contributes
      nothing

## 3. What the host hands over

- [x] 3.1 Write a test that shows a plugin searching the documents through the host
- [x] 3.2 Write a test that shows a plugin reading and writing what cora remembers
- [x] 3.3 Write a test that shows a plugin calling the model through the host
- [x] 3.4 Write a test that shows a plugin's log line is named for the plugin
- [x] 3.5 Write a test that shows a plugin reads a setting of its own, named for it
- [x] 3.6 Write a test that shows the host hands over cora's own ports, not copies of them

## 4. A refusal names the module

- [x] 4.1 Write a test that shows a module with no `extend` refused by name
- [x] 4.2 Write a test that shows a module whose `extend` raises refused by name, with the
      reason
- [x] 4.3 Write a test that shows a tool name cora offers itself refused by name
- [x] 4.4 Write a test that shows one name registered by two plugins refused, naming both
- [x] 4.5 Write a test that shows a registration refused before any turn runs

## 5. A tool that runs a turn of its own

- [x] 5.1 Write a test that shows a fixture plugin's tool running a bounded loop with the
      model
- [x] 5.2 Write a test that shows that loop's steps in the trace as children of the call
- [x] 5.3 Write a test that shows the loop offered no tool of cora's that writes or
      stops the turn
- [x] 5.4 Write a test that shows the loop's budget is its own, and the turn's is untouched
- [x] 5.5 Write a test that shows a nested step surviving a checkpoint and the conversation
      store
- [x] 5.6 Write a guard that shows nothing under `src/cora/` names a plugin, so the
      sub-agent fixture is written against the host rather than known to it
      changed

## 6. The plugins cora ships

- [x] 6.1 Write a test that shows the fitness plugin registering its tools, instructions
      and rule
- [x] 6.2 Write a test that shows the security plugin registering its rule alone
- [x] 6.3 Write a guard that shows no module in the repository defines a `PLUGIN` record

## 7. The marker comes off

- [x] 7.1 Drop 1.1's `xfail` marker and watch the outer test pass

## 8. What the build turned up

- [x] 8.1 Write a test that shows what a tool did inside its call reaching the page's
      wire as that call's own steps
- [x] 8.2 Write a test that shows a delegated loop's answer citing no number the turn
      handed out
- [x] 8.3 Write a test that shows a tool delegating inside a delegated loop keeping its
      own steps
- [x] 8.4 Write a test that shows a loop spending no more rounds than the host allows
- [x] 8.5 Write a test that shows what a plugin was holding staying out of the refusal
      the user reads
- [x] 8.6 Write a test that shows a plugin registering what it may not refused from the
      module path a deployment types
- [x] 8.7 Write a test that shows a plugin that registered nothing still announced
- [x] 8.8 Write tests that show a plugin reading the settings named for it, none of
      cora's own, and two plugins named alike refused
- [x] 8.9 Write a test that shows the page drawing what a step did inside it
- [x] 8.10 Write a test that shows a delegated loop reading its passages by document
      rather than by number
- [x] 8.11 Write a test that shows a number a loop invented stripped and its lines left
      alone
- [x] 8.12 Write a test that shows a loop and everything it delegates sharing one
      allowance
- [x] 8.13 Write a test that shows two modules named alike at the end refused at loading
- [x] 8.14 Write a test that shows a payload rendering itself for a reader that cannot
      cite, with the user's own numbering intact
- [x] 8.15 Write a test that shows an answer that cited nothing coming back as written


## 9. What the review turned up

- [x] 9.1 Write a test that shows a delegated loop reading its passages behind the same
      untrusted label a turn's own search gets
- [x] 9.2 Write a test that shows what a delegated loop answered reaching the outer
      model labelled as the document data it was built from
- [x] 9.3 Extract what a round records — a decision from a reply, a step and a message
      from a result — so the graph's round and a delegated one are written once
- [x] 9.4 Write a test that shows a loop that ran out of rounds telling the outer model
      what happened in a sentence
- [x] 9.5 Write a test that shows a delegated loop offered a search whose description
      matches what it is handed
- [x] 9.6 Write a test that shows a plugin's own tool called rather than shadowed when
      it takes a name cora's delegated search also uses
- [x] 9.7 Write a test that shows a rule that cannot screen refused at registration, and
      the same for instructions that are not a string
- [x] 9.8 Write a test that shows a step equal to itself after a checkpoint, and restore
      1085's assertion to equality
- [x] 9.9 Write a test that shows a line the loop wrote left alone when the bracketed
      number on it was never a citation
- [x] 9.10 Write a test that shows a turn stored before the trace was a tree read back
- [x] 9.11 Correct what `MAX_DELEGATED_ROUNDS` claims a turn can spend
- [x] 9.12 Wire `tools_only` back into a test or delete it
- [x] 9.13 Not done, and why: a suite registering against the real host is what proves
      the plugin works with cora, and a hand-written one would prove less. The package
      description said "no engine" of its tests as well as itself, and that is what was
      wrong; it now says which half it means
- [x] 9.14 Say what `5.6`'s guard proves, and what it does not
- [x] 9.15 Correct the prefix-bleed justification in `plugin_settings`
- [x] 9.16 Note the brief's headings changing with the plugin's name in `design.md`
- [x] 9.17 Drop `Registry.modules`, which nothing reads
- [x] 9.18 Rename `assemble`'s `plugin_settings` parameter, which shadows the function
- [x] 9.19 Announce what loaded before a plugin can fail registering
- [x] 9.20 Done in the panel rather than the recorder: emptying a detail that repeats
      its outcome empties a failed call's refusal with it, which three tests hold as the
      spec. The recorder keeps it, and `PlanPanel` declines to draw a row the line above
      already reads out
- [x] 9.21 Put step 5's snippet inside an `extend` in the how-to

## 10. What the second review turned up

- [x] 10.1 Write a test that shows a loop reading through a loop labelling what comes
      back, one hop further in than 9.1 reached
- [x] 10.2 Write a test that shows a plugin searching the documents itself marking the
      call, so the label hangs off the search rather than off `delegate`
- [x] 10.3 Write a test that shows a number after bold, a percent or a backtick still
      taken for the citation it is
- [x] 10.4 Write a test that shows a fence closed by the marker that opened it
- [x] 10.5 Write a test that shows a rule class registered in place of an instance
      refused
- [x] 10.6 Say what a `TraceStep` subclass owes `__post_init__`, and why the cache is
      keyed by class
- [x] 10.7 Drop `Inside.__iter__`, which nothing reads and which makes the record read
      as a sequence
- [x] 10.8 Keep `assemble`'s parameter name and alias the import instead, so the shadow
      goes without the name getting vaguer
- [x] 10.9 Say what reading `Host.documents` means, on the port a plugin reads
