Every item is one failing test. Group 2 runs before anything is deleted — a deleted test
is not a passing test. The pages and the `Makefile` are rewritten inside the green step
that needs them, because no test can fail for prose.

## 1. The outer test

- [x] 1.1 **Outer.** Write a test that shows nothing in the repository imports Streamlit —
      not the packages, not the tests, not the tooling. Mark it
      `@pytest.mark.xfail(strict=True)`
- [x] 1.2 *(discovered at 1.1)* Write a test that shows the repository walk finds the
      tree it claims to read — a walker returning nothing would let 1.1 pass on an empty
      list the day its marker comes off

## 2. What the removed app proved, over the shell's API

- [x] 2.1 Write a test that shows a fact told in one session briefs the model in the next,
      driven through the shell's API over one memory store
- [x] 2.2 Write a test that shows clearing memory empties the store and the next brief,
      driven the same way
- [x] 2.3 Write a test that shows a turn's steps reach the page with their tool arguments
      and their results, read off the frames the shell streams
- [x] 2.4 Port the live whole-session test — upload, ask, calculate, remember — to the
      shell's API, on the `llm` tier
- [x] 2.5 Port the live test that a real model answers from the documents but greets
      without them
- [x] 2.6 Port the live test that a real model asks for documents rather than answering
      without them
- [x] 2.7 Port the live test that a real model keeps what it is told and uses it next
      session
- [x] 2.8 Port the live test that a real model cites a passage the reader can open
- [x] 2.9 Port the live test that a real model asks which value to use instead of picking
      one

## 3. One start command

Dropped in review. This group was a guard over the `Makefile` — that `run` names the
React server, that no recipe starts Streamlit, that `run` builds the page first, and
that every `make <target>` a page gives is one the file defines. It was written, it was
green, and it was removed: ninety lines of Makefile parser and Markdown scanner for
claims a person checks by running the thing. The `Makefile` and the pages changed with
this story either way; nothing asserts them.

## 4. The member is gone

- [x] 4.1 Write a test that shows the workspace ships one frontend member, and it is the
      React one
- [x] 4.2 Write a test that shows no package in the workspace resolves Streamlit as a
      dependency — the bar is the whole tree, not `cora` alone

## 5. Done

- [x] 5.1 Drop 1.1's `xfail` marker and watch the outer test pass
