Every item is one failing test. Item 1.1 is the outer functional test, and the last item
drops its marker. New tests land in `tests/guards/test_front_door.py` unless an item names
another file.

## 1. The outer test

- [x] 1.1 Write the outer test — the front door's first screen carries all six parts: the
      problem, who it is for, how a turn works, what writing a plugin involves with its
      how-to linked, the absences block, and the showcase link. Mark it
      `@pytest.mark.xfail(strict=True)`; see it fail for the right reason and leave it red

## 2. The sentence, and the copies that follow it

- [x] 2.1 Change `README.md`'s opening sentence to the sprint's *Purpose* sentence and run
      `tests/guards/test_tagline.py` — the test that fails is the existing one, naming
      `docs/index.md`, `pyproject.toml`, `mkdocs.yml` and `CLAUDE.md` as copies left
      behind. Green when all four carry the new wording

## 3. The first screen, one part at a time

- [x] 3.1 Write a test that shows the front door states the problem, who it is for, and how
      a turn works — the core and what a plugin contributes — above the quick start
- [x] 3.2 Write a test that shows the front door says what writing a plugin involves and
      links `docs/how-to/write-a-plugin.md` above the quick start
- [x] 3.3 Write a test that shows the front door carries a block of what cora does not
      have, and that every item in it carries its reason beside it
- [ ] 3.4 Write a test that shows the guard rejects a bare absence — an item with a bold
      lead-in and nothing after the dash fails, so 3.3 cannot pass vacuously
- [ ] 3.5 Write a test that shows the front door links `showcase.turingcollege.com`, and
      that the link is above the quick start rather than anywhere in the file

## 4. Done

- [ ] 4.1 Drop the `xfail` marker from 1.1 and watch the outer test pass
