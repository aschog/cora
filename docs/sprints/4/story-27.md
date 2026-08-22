# Story 27: every drawing is read out of the code it is about

**As a** developer reading the docs · **I want** the pictures to be generated from the
source · **So that** what they show is what the code does, and cannot quietly stop being

> **Given** the walkthrough page's four sequences and the map page's two
> **When** a call, a branch, a graph edge or a port changes in the source
> **Then** `make diagram` redraws the page, and a guard fails until the committed drawing
> matches — including when the drawing would be *fresh but wrong*

Retires the standing decision that a sequence must stay hand-drawn (story 25): it holds of
the import graph, not of the source. A method body is an ordered list of calls, and
`LangGraphRunner._graph` declares the turn's own loop and routes.

## Test list

**Tiers:** unit unless marked — **(int)** integration.

#### The outer test

- [x] the walkthrough page shows four committed SVGs, each one what the generator writes
      today, and no page on the site draws a diagram by hand

#### Reading a sequence out of a method (`scripts/sequences.py`)

- [x] the upload sequence is the calls `add_file` makes, in the order it makes them
- [x] a lifeline is named for the field and for whatever the composition root puts behind
      it, not for the annotation
- [x] the caller is the package every call site shares, so naming one frontend does not
      draw half of them
- [x] a value the method constructs is no participant — a lifeline for `CitableHits` would
      put a domain value among the objects of a run
- [x] a reply is what the interface says it answers with, where nothing binds it
- [x] a reply belongs to the outermost call of a statement — the inner ones are the
      arguments it was given
- [x] the model is drawn answering: `chat_model.complete` has a reply
- [x] what stands behind a port the composition root fills inside itself is read off
      `assemble`, not declared — a wrapper in front of the knowledge base is drawn
- [x] a slot filled by role is resolved within the class that holds it, so one keyword
      name cannot resolve two ways across the app

#### A branch is what the source says it is

- [x] the upload sequence has one fork per `if`, the repair's own included
- [x] a repair only reads what was never kept: the parse and the write stand inside the
      fork, never beside it
- [x] a paused turn is not drawn being recorded
- [x] a statement holding a fork the reader has no fragment for stops `make diagram`
      rather than drawing every arm of it as unconditional

#### The graph a turn is walked by (`LangGraphRunner._graph`)

- [x] every node and every route the runner declares is drawn
- [x] the loop's condition is the route that does not come back, read off the edge map
- [x] a second unconditional edge out of one node stops the drawing

#### Drawn as UML (`scripts/gen_session_maps.py`)

- [x] every message names a method the receiver really has
- [x] no label is drawn off the page — a message an object sends itself on the last
      lifeline still has room
- [x] a label that flies over a lifeline is read on ground of its own
- [x] each drawing carries its own `prefers-color-scheme` and paints no sheet
- [x] each drawing names what it shows, with one participant box per lifeline

#### One description of cora, in four places (`tests/guards/test_tagline.py`)

- [x] there is an opening paragraph to hold the copies to
- [x] the docs front page opens with `README.md`'s own words
- [x] the distribution's description opens with the same sentence
- [x] every built page carries it as its `site_description`
- [x] the briefing says the same thing

#### The tables no generator writes (`tests/guards/test_reference_tables.py`)

- [x] the route table is the routes the shell mounts
- [x] the port table has a row per port the engine talks through, and the sentence above
      it counts them

#### Mermaid retired

- [x] **(int)** every drawing a narrative page shows is built beside it
- [x] a link into another page lands on a heading that is there — `--strict` gates it
