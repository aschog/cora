## 1. The outer test

- [ ] 1.1 Write the outer functional test, `xfail(strict=True)`: a package folder
      with a relative import, dropped while serving, answers the next listing read.

## 2. Discovery

- [ ] 2.1 Write a test that shows the folder scan yields a directory holding
      `__init__.py` beside the `.py` files.
- [ ] 2.2 Write a test that shows a directory without `__init__.py` is ignored.
- [ ] 2.3 Write a test that shows a hidden or underscore-led directory is ignored.

## 3. Loading

- [ ] 3.1 Write a test that shows a dropped package loads, named for its folder,
      its source the folder's path.
- [ ] 3.2 Write a test that shows `from . import sibling` inside a dropped package
      resolves.
- [ ] 3.3 Write a test that shows a dropped package cannot shadow an installed
      module of the same name.
- [ ] 3.4 Write a test that shows a package whose import raises is refused naming
      the folder and the error.
- [ ] 3.5 Write a test that shows a failed package leaves `sys.modules` as it found
      it, submodules included.

## 4. The name faces every existing check

- [ ] 4.1 Write a test that shows a folder whose name is not an identifier is
      refused.
- [ ] 4.2 Write a test that shows a dropped package colliding with a named module's
      name is refused naming both.
- [ ] 4.3 Write a test that shows a package defining no `extend` is refused.
- [ ] 4.4 Write a test that shows a package asking for a contract cora does not
      offer is refused before `extend` runs.

## 5. The live folder

- [ ] 5.1 Write a test that shows the folder signature differs when a file is
      added, removed, or touched, and holds still otherwise.
- [ ] 5.2 Write a test that shows the holder recomposes on a changed signature and
      returns the same app on an unchanged one.
- [ ] 5.3 Write a test that shows a plugin dropped after composition is in the next
      listing read.
- [ ] 5.4 Write a test that shows a deleted plugin is out of the next listing read.
- [ ] 5.5 Write a test that shows an edited plugin's new behaviour serves the next
      turn.
- [ ] 5.6 Write a test that shows a broken drop refuses that read, and the prior
      set answers the one after the folder is fixed.
- [ ] 5.7 Write a test that shows an app taken before a change finishes its turn on
      the set it started with.
- [ ] 5.8 Write a test that shows named modules load once and survive every
      recomposition untouched.

## 6. Done

- [ ] 6.1 Drop the outer test's `xfail` marker and watch it pass.
