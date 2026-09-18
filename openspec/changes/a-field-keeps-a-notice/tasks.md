## 1. The outer test

- [ ] 1.1 Write the functional test where a notice written to a field is answered back to a later reader, stamped with the time cora took it, marked `@pytest.mark.xfail(strict=True)`.

## 2. Writing one and reading it back

- [ ] 2.1 Write a test that the notice of a field nobody has written to is answered as none rather than a failure.
- [ ] 2.2 Write a test that a notice written to a field is answered whole to whoever asks for it.
- [ ] 2.3 Write a test that a second notice replaces the first rather than being merged into it.
- [ ] 2.4 Write a test that two fields written a notice each answer their own.

## 3. The arrival cora wrote

- [ ] 3.1 Write a test that a notice is answered carrying the time cora took it, off a clock the test holds.
- [ ] 3.2 Write a test that a notice carrying a time of the writer's own is answered stamped with cora's.

## 4. A field of the composition

- [ ] 4.1 Write a test that a notice written to a name that is no field is refused, naming the fields there are.
- [ ] 4.2 Write a test that asking for the notice of a name that is no field is refused.
- [ ] 4.3 Write a test that a field brought by a plugin dropped into the folder takes a notice, nothing restarted.
- [ ] 4.4 Write a test that the notice of a field whose plugin went away is refused on the next request.

## 5. Small, and an object

- [ ] 5.1 Write a test that a notice past the ceiling is refused and the held notice still answers.
- [ ] 5.2 Write a test that a body that is not a JSON object is refused and the held notice is unchanged.
- [ ] 5.3 Write a test that a notice saying nothing about its length is refused.

## 6. Beside everything else

- [ ] 6.1 Write a test that a field's notice is empty again in a freshly composed app, nothing outliving the process.
- [ ] 6.2 Write a test that the notice route answers the methods it names and refuses the rest.

## 7. Close it

- [ ] 7.1 Drop the outer test's `xfail` marker and watch it pass.
