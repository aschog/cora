# Story 22: The page stops explaining itself, and a quotation looks like one

**As a** reader · **I want** the page to spend its space on my documents, my answer and my
facts rather than on explaining its own panels · **So that** what I came for is what I see,
and the passage an answer quotes reads as a quotation

> **Given** documents indexed, an answer with steps behind it, facts in memory and a plugin
> loaded
> **When** I read the page
> **Then** no panel, rail or menu carries a paragraph explaining itself

> **Given** a panel with nothing in it yet
> **When** I open it
> **Then** it is simply empty — its tab already says what belongs there

> **Given** an answer that cites a document
> **When** I open the citation
> **Then** the quoted passage is marked in a warm amber, and nothing above it counts the
> marks for me

> **Given** an answer that has landed
> **When** I look at the right-hand rail
> **Then** the tab over the steps is called **STEPS**

Closes the *Cheap, one chrome pass* block of `manual-test-findings.md` — #11, #7, #9a, #3c,
#6, #14, #1. Nothing here is behaviour: it is ten deletions, a caption, a label and a
colour. It is one story because they are one pass over the same chrome, and three of them
touch the same vitest assertions. Each deletion takes its style rule with it —
`.plan-footer`, `.rail-note`, `.plugin-menu-foot`, `.panel-intro`, `.rail-empty` and
`.plugin-menu-heading` have no other caller — which no test can say, so it is not on the
list.

Three decisions the findings left open:

- **The empty states go too.** #7 kept them on the grounds that they earn their words; they
  do not. Four panels each explain what will arrive in them (`SourcePanel`, `PlanPanel`,
  `SessionsPanel`, `MemoryPanel`), the documents rail says `Nothing indexed yet.` above the
  control that fixes it, and the tab or heading that opened each already named it. An empty
  panel is empty.
- **`not cited in this answer` stays.** #6 removes only the counting branch; the other one
  carries information a reader cannot see for themselves, and the case it speaks for stays
  exceptional until #3 makes every document openable.
- **The palette gains one warm token**, `--amber: #d29922` on `--amber-tint: #241a08` —
  the same family the blues already come from, so it sits beside `--accent` rather than
  arriving from somewhere else. `--magenta` is spoken for by destructive actions.

## Test list

**Tiers:** unit unless marked — **(ui)** vitest via `make ui-test`, **(br)** Chromium via
`make ui-test-browser`.

#### Nothing in the page explains the page (`ui/src/App.test.tsx`) **(ui)**

One list of every deleted sentence, asserted from the page rather than per component, so a
paragraph reintroduced anywhere fails whichever panel it lands in (`EXPLANATIONS`):

- [x] a page with steps, facts, a plugin and a past conversation explains none of them
      (`FOOTER`, `INTRO`, `HEADING`, `FIXED`)
- [x] a page with nothing in it yet draws its controls and no prose (`NOTHING` × 4)

#### The one state the page-level tests cannot reach (`ui/src/components/DocumentRail.test.tsx`) **(ui)**

The App fixture serves one document, and citing it is what makes the rail openable — so a
rail holding a cited *and* an uncited document exists only here, and it is the only state
the greying note ever appeared in:

- [x] a rail holding both draws the list and no note about greying (`UNCITED`)
- [x] the uncited one cannot be opened and the cited one can — the note's own claim, left
      standing by its deletion
- [x] nothing indexed yet draws the upload control alone

#### The source pane is found by what it opened on (`ui/src/components/SourcePanel.tsx`) **(ui)**

- [x] the pane names its document as a heading — the rail draws the same filename, so the
      text alone cannot say which pane is open
- [x] a document with a cited passage draws the mark and no count above it
- [x] a document the answer did not rest on still says so
- [x] the four `App.test.tsx` tests that used the count as their proxy ask for something
      that means what they were after: two for the heading, two for the document's text and
      the mark on it

#### The tab claims what it shows (`ui/src/App.tsx`) **(ui)**

- [x] the tab over the steps reads `STEPS`, and an answer landing selects it — one union
      member, two `setTab` calls, six `role="tab"` lookups

#### A quotation is not a control (`ui/src/styles.css`) **(br)**

- [x] a cited passage's tint and left rule are the warm token, not the accent the page uses
      for links, focus rings and the send button — asserted where the cascade is real

#### Outer functional tests

- [x] **(ui)** a full page — documents, steps, facts, a plugin — carries no paragraph
      explaining any of them, and the source pane opens under its filename with no count
- [x] **(ui)** a page with nothing in it yet — nothing indexed, no steps, no facts, no
      conversations — draws no paragraph either, only the controls that fill it
- [x] **(br)** the passage a citation opens is amber, not the page's blue
