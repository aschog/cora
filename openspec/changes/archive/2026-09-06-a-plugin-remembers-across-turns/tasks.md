## 1. The outer test

- [x] 1.1 Write the functional test where a plugin keeps a value on one turn and a later turn of that conversation reads it back, marked `@pytest.mark.xfail(strict=True)`.

## 2. The state it rides on

- [x] 2.1 Write a test that the turn's state carries what each plugin kept, by plugin name.
- [x] 2.2 Write a test that it is not emptied at the top of a turn, as `filled` is.
- [x] 2.3 Write a test that it survives a checkpoint and comes back equal to what was kept.
- [x] 2.4 Write a test that a deployment checkpointing to a file reads it back in a new process.

## 3. Reading and writing during a call

- [x] 3.1 Write a test that a tool call reads what was kept before the call began.
- [x] 3.2 Write a test that what a call wrote is in the state after the step, beside `filled`.
- [x] 3.3 Write a test that keeping nothing under a name drops what was there.
- [x] 3.4 Write a test that a name nothing was kept under reads back as nothing.
- [x] 3.5 Write a test that a delegated loop inside a call reads and writes the same snapshot.
- [x] 3.6 Write a test that the binding is reset after the call, so the next call is not the previous one's.
- [x] 3.7 Write a test that a call that refused still keeps what it wrote before it refused.

## 4. What a plugin is handed

- [x] 4.1 Write a test that `Host.state` reads and writes under the plugin's own name.
- [x] 4.2 Write a test that two plugins keeping the same name each read back their own value.
- [x] 4.3 Write a test that a plugin cannot name a conversation, only a key.

## 5. Outside a turn

- [x] 5.1 Write a test that a write inside `extend` is dropped and the plugin still loads.
- [x] 5.2 Write a test that a read outside a call comes back with nothing.

## 6. Two conversations

- [x] 6.1 Write a test that a second conversation reads nothing of the first one's values.
- [x] 6.2 Write a test that deleting a conversation leaves the other's values alone.
- [x] 6.3 Write a test that a new conversation on a deleted thread reads nothing under the name.

## 7. Close it

- [x] 7.1 Drop the outer test's `xfail` marker and watch it pass.
