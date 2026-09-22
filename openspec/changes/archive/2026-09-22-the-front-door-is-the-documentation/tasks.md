## 1. The front door's links resolve

- [x] 1.1 Write the outer guard asserting every `docs/` path `README.md` links names a file
      the repository holds, marked `@pytest.mark.xfail(strict=True)`.
- [x] 1.2 Mutate `README.md` to link a page that does not exist and see the guard fail
      naming that page.

## 2. The front door carries the commands

- [x] 2.1 Write a guard asserting every `make` target `README.md` names is one the
      `Makefile` defines, and see it fail on a target the repository does not have.
- [x] 2.2 Write a guard asserting every `CORA_*` name `README.md` carries is one
      `cora.app.config` reads, and see it fail on an invented variable.

## 3. Done

- [x] 3.1 Drop the `xfail` marker from 1.1 and watch the outer guard pass against the
      README as it stands.
