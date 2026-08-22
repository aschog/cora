# Story 27: every drawing is read out of the code it is about

**As a** developer reading the docs · **I want** the pictures to be generated from the
source · **So that** what they show is what the code does, and one command puts them back
in step

> **Given** the walkthrough page's four sequences and the map page's two
> **When** a call, a branch, a graph edge or a port changes in the source
> **Then** `make diagram` redraws every drawing off the code as it now stands

Retires the standing decision that a sequence must stay hand-drawn (story 25): it holds of
the import graph, not of the source. A method body is an ordered list of calls, and
`LangGraphRunner._graph` declares the turn's own loop and routes.

## Test list

**Tiers:** unit unless marked — **(int)** integration.

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

#### Not guarded, by decision

The sequences themselves carry no tests: the four drawings are redrawn by `make diagram`
and read by whoever changed the code. The component map and the domain map keep theirs.
