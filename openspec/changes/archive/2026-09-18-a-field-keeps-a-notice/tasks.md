## 1. The outer test

- [x] 1.1 Write the functional test where a notice written to a field is answered back to a later reader, stamped with the time cora took it, marked `@pytest.mark.xfail(strict=True)`.

## 2. Writing one and reading it back

- [x] 2.1 Write a test that the notice of a field nobody has written to is answered as none rather than a failure.
- [x] 2.2 Write a test that a notice written to a field is answered whole to whoever asks for it.
- [x] 2.3 Write a test that a second notice replaces the first rather than being merged into it.
- [x] 2.4 Write a test that two fields written a notice each answer their own.
- [x] 2.5 Write a test that the field cora ships keeps a notice as a field a plugin brought does.

## 3. The arrival cora wrote

- [x] 3.1 Write a test that a notice's stamp lies between two readings of the clock around the write.
- [x] 3.2 Write a test that a notice carrying a time of the writer's own is answered stamped with cora's.

## 4. A field of the composition

- [x] 4.1 Write a test that a notice written to a name that is no field is refused, naming the fields there are.
- [x] 4.2 Write a test that asking for the notice of a name that is no field is refused.
- [x] 4.3 Write a test that a field brought by a plugin dropped into the folder takes a notice, nothing restarted.
- [x] 4.4 Write a test that the notice of a field whose plugin went away is refused on the next request.

## 5. Small, and an object

- [x] 5.1 Write a test that a notice past the ceiling is refused and the held notice still answers.
- [x] 5.2 Write a test that a body that is not a JSON object is refused and the held notice is unchanged.

## 6. Beside everything else

- [x] 6.1 Write a test that a field's notice is empty again in a freshly composed app, nothing outliving the process.
- [x] 6.2 Write a test that the notice route answers the methods it names and refuses the rest.
- [x] 6.3 Write a test that a notice is answered as JSON whatever it holds, a nested list included.

## 7. Close it

- [x] 7.1 Drop the outer test's `xfail` marker and watch it pass.

## Dropped

- A test that a notice saying nothing about its length is refused. The reader bounds the stream as it arrives, so a declared length buys nothing the ceiling does not already hold.
- A vitest over the dev server's proxy. The notice is under `/api`, which `vite.config.ts` already sends to cora.
