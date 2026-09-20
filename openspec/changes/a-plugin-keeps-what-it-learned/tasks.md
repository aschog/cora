## 1. The outer test

- [ ] 1.1 Write the functional test where a plugin keeps text in a turn, and reads it back in a later turn of another conversation, marked `@pytest.mark.xfail(strict=True)`.

## 2. The store

- [ ] 2.1 Write a test that what was kept under a name is read back from a fresh adapter over the same file.
- [ ] 2.2 Write a test that two plugins keeping under one name keep two values, and each reads its own.
- [ ] 2.3 Write a test that a name nothing was kept under reads as nothing.
- [ ] 2.4 Write a test that keeping nothing under a name drops it.
- [ ] 2.5 Write a test that a store that cannot be reached raises the failure cora reports rather than losing the write silently.

## 3. What the plugin is handed

- [ ] 3.1 Write a test that the host hands a plugin a store namespaced under the plugin's own name.
- [ ] 3.2 Write a test that a host built without a store hands the plugin nothing.

## 4. Assembled

- [ ] 4.1 Write a test that an app assembled with a store hands every plugin one, and one assembled without hands none.
- [ ] 4.2 Write a test that what a plugin kept is not in the brief and not in what cora recalls about the user.

## 5. Close it

- [ ] 5.1 Drop the marker and watch the outer test pass.
