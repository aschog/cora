## 1. The outer test

- [x] 1.1 Write the functional test where a plugin subscribed to the answer redacts a phone number, and the reader is given the redacted answer, marked `@pytest.mark.xfail(strict=True)`.

## 2. The point itself

- [x] 2.1 Write a test that the new name is one a plugin may subscribe to, and an unknown one is still refused.
- [x] 2.2 Write a test that a handler is given the answer as text.
- [x] 2.3 Write a test that what it hands back is what the turn answers with.
- [x] 2.4 Write a test that handing back nothing leaves the answer as it was.
- [x] 2.5 Write a test that adding the point cost `events.py` one entry and no branch.

## 3. Chaining and failing

- [x] 3.1 Write a test that two handlers each amend, in load order, and neither undoes the other.
- [x] 3.2 Write a test that a handler that raises is dropped and the turn still answers.
- [x] 3.3 Write a test that a handler handing back something that is not text is dropped.
- [x] 3.4 Write a test that a dropped handler is on the trace as failed, naming its plugin.
- [x] 3.5 Write a test that a handler that amended is on the trace as having changed the answer.

## 4. What follows the answer

- [x] 4.1 Write a test that citations are read off the amended answer, not the original.
- [x] 4.2 Write a test that removing a sentence removes the citation it carried.
- [x] 4.3 Write a test that the amended answer is what is recorded as the turn.
- [x] 4.4 Write a test that a turn resumed after a pause dispatches the point once, on its answer.

## 5. Scope

- [x] 5.1 Write a test that a handler registered under a scope runs only in turns of that scope.
- [x] 5.2 Write a test that a system-wide handler runs whatever the turn is running as.

## 6. Close it

- [x] 6.1 Drop the outer test's `xfail` marker and watch it pass.
