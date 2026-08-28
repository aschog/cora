## Context

Two frontends, one of them the one sprint 5 builds on. The other goes — with its tests,
its workspace member and its dependency — and what it proved is asserted through the
shell's HTTP surface before a line of it is deleted.

## Order

Port, then delete, in that order and not the other. A deleted test is not a passing test:
if the coverage moves after the app goes, the gap is invisible while it exists. Every
ported behaviour is green against the shell before `frontends/streamlit/` is touched.

## The coverage map

What the four AppTest files and the live tier held, and where each behaviour ends up.

- **Ported, new tests over the shell's API** — a fact told in one session briefs the model
  in the next, clearing memory empties the store and the next brief, and a turn's steps
  carry their tool arguments and their results.
- **Ported, same assertions over a new surface** — the six live-tier tests. The AppTest
  readers (`_answer`, `_opens_a_passage`, `_steps`) become frame readers, which
  `tests/acceptance/test_react_frontend.py` already has.
- **Already held** — a cited passage opens onto the text its offsets were measured in
  (`test_api.py`), the citation modal and the marked passage (the page's own tests), the
  three rails and the tab labels (the page's own tests), and a conversation that outlives
  the process (`test_api.py`'s sessions endpoints).
- **Dropped, and named in the proposal** — the session-state keys a click wrote, the tab
  list read off `at.tabs`, the column weights. Each was how one frontend was built, and
  the React page's tests make their own claims about its own shape.

## The seam

- **The `Makefile` is the one place a start command is written.** A page names a target,
  the target names the module. That indirection already exists — the README says the
  target survives a package move — so re-aiming one recipe re-aims every page quoting it.
- **The `Makefile` itself is unguarded, decided in review.** A guard over it was written
  and removed: parsing the file and scanning the pages for `make <target>` cost ninety
  lines to assert what running the thing shows. `test_docs.py` still holds the paths the
  pages claim.
- **The import bar already exists, scoped.** `test_architecture.py` has `_imports_streamlit`
  and asserts it stays inside the shell. The predicate stays and the scope widens to the
  whole tree — a rule that reads "nowhere" rather than "not there".

## Components

- `tests/guards/test_architecture.py` — `test_streamlit_stays_inside_the_ui_shell` becomes
  the repository-wide bar, and `UI_ROOT` and the per-package allowance go with the member.
- `tests/guards/test_packaging.py`, `test_installs.py`, `test_smoke.py`, `test_docs.py` —
  the member drops out of each list it is named in.
- `Makefile` — `run`/`run-env` become what `run-react`/`run-env-react` were, and `APP`,
  the two Streamlit recipes and the two React aliases go.
- The pages — the quick start, the tutorial and the two how-tos describe one screen.
  `docs/how-to/run-the-react-shell.md` keeps its path (the nav and `test_docs.py` name it)
  and narrows to the development loop, Vite on 5173, and why the server reads only the
  build.

## Trade-offs taken

- **Deleted now rather than frozen until the sprint's end.** A frozen frontend costs
  nothing to keep and something to remember: every core change of stories 4 and 5 —
  `ports.plugin.Plugin` becomes `Host` — would have to keep it compiling, for code no one
  runs. The removal was the sprint's declared slack, and spending it early means nothing
  is pre-designated if the sprint runs long.
- **The live tier is ported, not dropped.** It is the only tier that fails for wording, and
  the shell's API is a better surface for it than a page-render harness: what it asserts is
  what the model did, and the frames carry that without a widget in between.
- **`run` keeps building the page first.** The server reads `frontends/react/ui/dist` and
  nothing else, so a `run` that skipped the build would serve yesterday's page and look
  like a caching bug rather than a missing step.

## Untouched

- No port changes and no engine changes: the deletion is a caller leaving, not a seam
  moving.
- The component map is regenerated rather than edited — it is read out of the code, and
  the guard beside it fails while it is behind.
