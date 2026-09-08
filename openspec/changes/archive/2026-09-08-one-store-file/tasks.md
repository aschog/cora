## 1. The outer test

- [x] 1.1 Write the acceptance test — an assembled app keeps its facts, turns,
  checkpoints and passages in the one file the setting names, with no second database
  file beside it — marked `@pytest.mark.xfail(strict=True)`.

## 2. One setting names it

- [x] 2.1 Write a config test that the database defaults to `.cora/cora.sqlite`.
- [x] 2.2 Write a config test that the two retired variables are read by nothing.
- [x] 2.3 Write a config test that a blanked `CORA_DB_PATH` falls back to the default.
- [x] 2.4 Write a config test that the configuration carries one store path and not
  three.
- [x] 2.5 Rewrite the test that held the stores beside one another, so it holds the
  documents root and the database in one directory.

## 3. Every store at that file

- [x] 3.1 Write a test that a remembered fact is read back out of the file the setting
  names.
- [x] 3.2 Write a test that a recorded turn is read back out of that same file.
- [x] 3.3 Write a test that a parked thread resumes out of that same file.
- [x] 3.4 Write a test that an indexed passage is searched out of that same file.
- [x] 3.5 Write a test that a write to each of the four leaves the other three readable.

## 4. Deleting stays whole

- [x] 4.1 Write a test that deleting a conversation takes its turns and its checkpoint
  and leaves the facts.
- [x] 4.2 Write a test that forgetting a fact leaves the turns and the passages.

## 5. What the page promises

- [x] 5.1 Write a guard assertion that the store discovery no longer lists the retired
  variables.
- [x] 5.2 Rewrite the privacy page's store table until its guard passes.

## 6. Done

- [x] 6.1 Drop the `xfail` marker from 1.1 and watch the outer test pass.

## 7. Review findings

- [x] 7.1 Write a test that each store opens the shared file in write-ahead mode, which
  SQLite's own default is not.
- [x] 7.2 Give the four writers one `connect`, so the journal mode is cora's own doing
  rather than a library's incidental pragma.
- [x] 7.3 Prefix `turns` as the retriever's tables are prefixed, so every table cora
  owns is named apart from the libraries sharing the file.
- [x] 7.4 Fold the third copy of the test configuration into the shared helper.
- [x] 7.5 Write a test per store that a path whose directory cannot be made surfaces as
  the error its own port promises, rather than as a bare `OSError`.
