Almost no test list. The subject of this change is one written page, and a `.md` file is
not test-backed — it is held by a person reading it. One claim is machine-readable, and a
guard is a test, so it is an item.

## 1. What cora keeps, held against the settings

- [x] 1.1 **Guard.** The privacy page naming every location a deployment can configure
      and the variable that moves it, discovered from `cora.app.config` rather than
      listed — so a store that moves, a store that is added, or a variable renamed is
      red until the page says so

The locations guard alone holds nothing here, which is what 1.1 exists for: every store
is made at runtime and is untracked, so naming one as a directory would claim a path a
clean checkout does not have. That a setting is really read under the name 1.1 derives is
`tests/cora/app/test_config.py`'s to hold, and it does — a renamed variable already fails
there, so this change adds no second test for it.

Everything else is prose. Done is the page answering the story's criteria, checked in
review against `specs/disclosure/spec.md` — and the criterion that matters most cannot be
automated at all, because it asks whether the claims are *true*.
