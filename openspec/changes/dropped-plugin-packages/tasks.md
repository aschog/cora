## 1. The outer test

- [x] 1.1 Write the outer functional test, `xfail(strict=True)`: a package folder
      with a relative import, dropped while serving, answers the next listing read.

## 2. Discovery

- [x] 2.1 Write a test that shows the folder scan yields a directory holding
      `__init__.py` beside the `.py` files.
- [x] 2.2 Write a test that shows a directory without `__init__.py` is ignored.
- [x] 2.3 Write a test that shows a hidden or underscore-led directory is ignored.

## 3. Loading

- [x] 3.1 Write a test that shows a dropped package loads, named for its folder,
      its source the folder's path.
- [x] 3.2 Write a test that shows `from . import sibling` inside a dropped package
      resolves.
- [x] 3.3 Write a test that shows a dropped package cannot shadow an installed
      module of the same name.
- [x] 3.4 Write a test that shows a package whose import raises is refused naming
      the folder and the error.
- [x] 3.5 Write a test that shows a failed package leaves `sys.modules` as it found
      it, submodules included.

## 4. The name faces every existing check

- [x] 4.1 Write a test that shows a folder whose name is not an identifier is
      refused.
- [x] 4.2 Write a test that shows a dropped package colliding with a named module's
      name is refused naming both.
- [x] 4.3 Write a test that shows a package defining no `extend` is refused.
- [x] 4.4 Write a test that shows a package asking for a contract cora does not
      offer is refused before `extend` runs.

## 5. The live folder

- [x] 5.1 Write a test that shows the folder signature differs when a file is
      added, removed, or touched, and holds still otherwise.
- [x] 5.2 Write a test that shows the holder recomposes on a changed signature and
      returns the same app on an unchanged one.
- [x] 5.3 Write a test that shows a plugin dropped after composition is in the next
      listing read.
- [x] 5.4 Write a test that shows a deleted plugin is out of the next listing read.
- [x] 5.5 Write a test that shows an edited plugin's new behaviour serves the next
      turn.
- [x] 5.6 Write a test that shows a broken drop refuses that read, and the prior
      set answers the one after the folder is fixed.
- [x] 5.7 Write a test that shows an app taken before a change finishes its turn on
      the set it started with.
- [x] 5.8 Write a test that shows named modules load once and survive every
      recomposition untouched.

## 6. A dropped field is offered

- [x] 6.1 Write a test that shows assemble offers the given scopes plus those
      registered by the plugins it is told bring their own, carried on the app.
- [x] 6.2 ~~A named module's unconfigured scope stays unoffered~~ — superseded by
      7.2: the union rule reversed this, and the test went with it.
- [x] 6.3 Write a test that shows a dropped plugin's scope is in the holder's next
      composition and gone once the plugin is deleted.
- [x] 6.4 Write a test that shows the offered-fields route reads the current
      composition.
- [x] 6.5 Write a test that shows a question pinned to a dropped field is accepted.
- [x] 6.6 Write a test that shows the rails list and upload into a dropped field.
- [x] 6.7 Extend the outer test: the dropped package's field is offered on the next
      read.

## 7. One rule for fields

- [x] 7.1 Write a test that shows the offered fields are the configured ones plus
      every scope any loaded plugin registered, in that order, named once.
- [x] 7.2 Write a test that shows a named module's field is offered without
      configuration, exactly as a dropped one's is.
- [x] 7.3 Write a test that shows a configured field with no registration is still
      offered — a documents-only field.
- [x] 7.4 Write a test that shows a symlinked package directory loads as a plugin
      and an edit through the link moves the signature.

## 8. Review findings

- [x] 8.1 Write a test that shows a slow drop recomposing inside an async handler
      does not stall the event loop.
- [x] 8.2 Write a test that shows recomposition reuses the process checkpointer.
- [x] 8.3 Write a test that shows a dropped plugin's tool answers the next turn, and
      an edit to it is what the turn after that executes.

- [x] 8.4 Write a test that shows a dropped file and package sharing a name are
      refused naming both.
- [x] 8.5 Write a test that shows a broken symlink in the folder is not a plugin.

## 9. Done

- [x] 8.1 Drop the outer test's `xfail` marker and watch it pass.
