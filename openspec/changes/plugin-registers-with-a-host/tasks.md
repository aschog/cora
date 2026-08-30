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
- [x] 5.6 Write a guard that shows the sub-agent fixture needs nothing under `src/cora/`
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

