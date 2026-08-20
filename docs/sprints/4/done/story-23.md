# Story 23: What an upload did is said beside the list it changed

**As a** reader who has just handed cora a file · **I want** to be told what became of it
where the file was going · **So that** I can see at a glance whether my documents grew, and
put the sentence away when I have read it

> **Given** a document the store does not have
> **When** I add it from the documents rail
> **Then** the rail says it was added and how many passages it holds, in the page's own
> accent

> **Given** a document the store already has
> **When** I add it again
> **Then** the rail says so in the colour and with the mark the page keeps for an outcome I
> did not ask for — it is not the same news as a document added

> **Given** either sentence on screen
> **When** I have read it
> **Then** I can shut it, and it goes

Closes no finding: #2 shipped the notice itself in `done/story-21.md`, and this is the shape
it should have had. Recorded after it was built, from a mockup handed over mid-branch — so
the list below is what the tests assert, not a plan they were written from.

Two decisions, one of which reverses `done/story-21.md`:

- **A duplicate wears the destructive colour.** Story 21 drew the notice in `--accent`
  deliberately, on the grounds that a duplicate "is news rather than trouble". That is
  reversed here: an upload that indexed nothing is not the outcome the reader asked for, and
  the mockup says so with `--magenta` and an alarm mark. The test that encoded the old
  decision was rewritten to the new claim rather than deleted.
- **The tone splits by outcome, rather than the whole notice going magenta.** One piece of
  state carries both sentences, so `Added "notes.md" — 12 passages.` would otherwise arrive
  in an error's clothes. `wrong` is the flag, and only it takes the mark and the colour.

The notice leaves the page-wide `.banners` strip for the rail, which means it is not drawn
while that rail is collapsed. Uploading is only possible from the rail, so the only way to
reach that is to collapse it mid-ingestion.

## Test list

**Tiers:** **(ui)** vitest via `make ui-test`.

#### The sentence sits beside the list it is about (`ui/src/App.test.tsx`) **(ui)**

- [x] what an upload did is drawn inside the documents rail, and the banner strip is empty
- [x] a document added names itself and its passage count, quoted
- [x] one passage indexed is one passage, not one passages

#### It is announced, not only shown (`ui/src/components/DocumentRail.test.tsx`) **(ui)**

The colour and the mark carry the outcome for a reader who can see them; a live region is
the only channel that carries it for one who cannot — and a region mounted together with its
first sentence is not one:

- [x] the rail holds the region before there is anything to announce, and it is empty
- [x] the sentence arrives inside that same region
- [x] the page's own notices strip and this one are told apart by name, not by role

#### The two outcomes look different (`ui/src/components/UploadNotice.tsx`) **(ui)**

- [x] a duplicate is marked `wrong`; a document added is not — one test, both outcomes, so
      neither can drift into the other's clothes
- [x] a file uploaded twice is added, and then said to be there already

#### The reader can put it away (`ui/src/components/UploadNotice.tsx`) **(ui)**

- [x] a dismiss control shuts the sentence, whichever outcome it carries

#### What already held, and still does (`ui/src/App.tsx`) **(ui)**

- [x] an upload that fails says so, and takes the last one's notice away
- [x] a refusal from a conversation the reader has left does **not** take away news about an
      upload that worked in the one they are in — the clear is stamped like the notice
- [x] starting a new session takes the notice away, and reopening an earlier conversation
      does too
- [x] a notice stands while the reader asks their next question
- [x] a notice for an upload the reader walked away from is not drawn
