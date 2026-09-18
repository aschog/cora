## Why

The plan the trainer works from is written into the page, so changing what you train
takes an edit to a file inside a plugin rather than a row in a spreadsheet.

## What Changes

- The trainer reads its plan from a published sheet each time it is opened
- A sheet that cannot be read costs nothing: the plan last seen stands, then the built-in one
- The strip says when it is training from the plan in the page rather than the sheet
- The plan already worked keeps its progress when a sheet swaps the exercises under it
- The page asks the sheet itself, that sheet answering any origin, so cora proxies nothing
- The plan shipped in the page stays what it is: the fallback, in the coach's own language
- Capability `plugins` — what the fitness field's page takes its plan from

## Impact

- `plugins/fitness/src/cora/plugins/fitness/page/index.html` — the sheet, parsed and adopted
- `plugins/fitness/tests/fitness/test_plugin.py` — a fifth host, and what it is for
- `frontends/react/ui/e2e/trainer.spec.ts` — the parsing, and a sheet that is not there
- `docs/what-ships-with-it.md` — where the plan comes from and how to point it elsewhere
- Left alone: the workout, which still goes to cora and nowhere else
- Left alone: the built-in plan, which is what a page with no sheet trains from
