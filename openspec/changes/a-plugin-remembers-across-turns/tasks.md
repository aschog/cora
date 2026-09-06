## 1. The outer test

- [ ] 1.1 Write the functional test where a plugin keeps a value on one turn and a later turn of that conversation reads it back, marked `@pytest.mark.xfail(strict=True)`.

## 2. The port and its adapter

- [ ] 2.1 Write a test that a value kept under a name reads back as that value.
- [ ] 2.2 Write a test that a name nothing was kept under reads back as nothing.
- [ ] 2.3 Write a test that keeping nothing under a name drops what was there.
- [ ] 2.4 Write a test that two conversations keeping the same name hold two values.
- [ ] 2.5 Write a test that the adapter writes into the file the conversation's turns are in.

## 3. The conversation reaches the call

- [ ] 3.1 Write a test that the turn carries the conversation it belongs to, seeded where the question is.
- [ ] 3.2 Write a test that a tool call runs with that conversation bound, beside the fields it already binds.
- [ ] 3.3 Write a test that a delegated loop inside a call keeps under the same conversation.
- [ ] 3.4 Write a test that the binding is reset after the call, so the next call is not the previous one's.

## 4. What a plugin is handed

- [ ] 4.1 Write a test that `Host.state` reads and writes under the plugin's own name.
- [ ] 4.2 Write a test that two plugins keeping the same name each read back their own value.
- [ ] 4.3 Write a test that a plugin cannot name a conversation, only a key.
- [ ] 4.4 Write a test that a deployment binding no store leaves `Host.state` reading nothing.

## 5. Outside a turn

- [ ] 5.1 Write a test that a write inside `extend` is dropped and the plugin still loads.
- [ ] 5.2 Write a test that a read outside a call comes back with nothing.

## 6. Forgetting

- [ ] 6.1 Write a test that deleting a conversation drops what its plugins kept in it.
- [ ] 6.2 Write a test that deleting one conversation leaves another conversation's values alone.
- [ ] 6.3 Write a test that a store that fails to drop does not lose the turns or the thread.

## 7. Close it

- [ ] 7.1 Drop the outer test's `xfail` marker and watch it pass.
