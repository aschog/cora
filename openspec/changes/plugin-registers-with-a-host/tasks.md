Every item is one failing test, and group 2 comes first because the rest register through
it.

## 1. The outer test

- [ ] 1.1 **Outer.** Write a test that shows a fixture plugin registering a tool, an
      instruction and a rule through `extend`, and a turn using all three. Mark it
      `@pytest.mark.xfail(strict=True)`

## 2. The host and what registering means

- [ ] 2.1 Write a test that shows a module's `extend` is called with a host when it loads
- [ ] 2.2 Write a test that shows a registered tool is offered to the model
- [ ] 2.3 Write a test that shows registered instructions reach the brief under the
      plugin's heading
- [ ] 2.4 Write a test that shows a registered rule screens what the user types
- [ ] 2.5 Write a test that shows every registration carries the module that made it
- [ ] 2.6 Write a test that shows a module registering nothing loads and contributes
      nothing

## 3. What the host hands over

- [ ] 3.1 Write a test that shows a plugin searching the documents through the host
- [ ] 3.2 Write a test that shows a plugin reading and writing what cora remembers
- [ ] 3.3 Write a test that shows a plugin calling the model through the host
- [ ] 3.4 Write a test that shows a plugin's log line is named for the plugin
- [ ] 3.5 Write a test that shows a plugin reads a setting of its own, named for it
- [ ] 3.6 Write a test that shows the host hands over cora's own ports, not copies of them

## 4. A refusal names the module

- [ ] 4.1 Write a test that shows a module with no `extend` refused by name
- [ ] 4.2 Write a test that shows a module whose `extend` raises refused by name, with the
      reason
- [ ] 4.3 Write a test that shows a tool name cora offers itself refused by name
- [ ] 4.4 Write a test that shows one name registered by two plugins refused, naming both
- [ ] 4.5 Write a test that shows a registration refused before any turn runs

## 5. A tool that runs a turn of its own

- [ ] 5.1 Write a test that shows a fixture plugin's tool running a bounded loop with the
      model
- [ ] 5.2 Write a test that shows that loop's steps in the trace as children of the call
- [ ] 5.3 Write a test that shows the loop offered only tools that read
- [ ] 5.4 Write a test that shows the loop's budget is its own, and the turn's is untouched
- [ ] 5.5 Write a test that shows a nested step surviving a checkpoint and the conversation
      store
- [ ] 5.6 Write a guard that shows the sub-agent fixture needs nothing under `src/cora/`
      changed

## 6. The plugins cora ships

- [ ] 6.1 Write a test that shows the fitness plugin registering its tools, instructions
      and rule
- [ ] 6.2 Write a test that shows the security plugin registering its rule alone
- [ ] 6.3 Write a guard that shows no module in the repository defines a `PLUGIN` record

## 7. The marker comes off

- [ ] 7.1 Drop 1.1's `xfail` marker and watch the outer test pass
