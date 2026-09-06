## 1. The outer test

- [ ] 1.1 Write the functional test where a plugin keeps a value on one turn and a later turn of that conversation reads it back, marked `@pytest.mark.xfail(strict=True)`.

## 2. The state it rides on

- [ ] 2.1 Write a test that the turn's state carries what each plugin kept, by plugin name.
- [ ] 2.2 Write a test that it is not emptied at the top of a turn, as `filled` is.
- [ ] 2.3 Write a test that it survives a checkpoint and comes back equal to what was kept.
- [ ] 2.4 Write a test that a deployment checkpointing to a file reads it back in a new process.

## 3. Reading and writing during a call

- [ ] 3.1 Write a test that a tool call reads what was kept before the call began.
- [ ] 3.2 Write a test that what a call wrote is in the state after the step, beside `filled`.
- [ ] 3.3 Write a test that keeping nothing under a name drops what was there.
- [ ] 3.4 Write a test that a name nothing was kept under reads back as nothing.
- [ ] 3.5 Write a test that a delegated loop inside a call reads and writes the same snapshot.
- [ ] 3.6 Write a test that the binding is reset after the call, so the next call is not the previous one's.
- [ ] 3.7 Write a test that a call that refused still keeps what it wrote before it refused.

## 4. What a plugin is handed

- [ ] 4.1 Write a test that `Host.state` reads and writes under the plugin's own name.
- [ ] 4.2 Write a test that two plugins keeping the same name each read back their own value.
- [ ] 4.3 Write a test that a plugin cannot name a conversation, only a key.

## 5. Outside a turn

- [ ] 5.1 Write a test that a write inside `extend` is dropped and the plugin still loads.
- [ ] 5.2 Write a test that a read outside a call comes back with nothing.

## 6. Two conversations

- [ ] 6.1 Write a test that a second conversation reads nothing of the first one's values.
- [ ] 6.2 Write a test that deleting a conversation leaves the other's values alone.
- [ ] 6.3 Write a test that a new conversation on a deleted thread reads nothing under the name.

## 7. Close it

- [ ] 7.1 Drop the outer test's `xfail` marker and watch it pass.
