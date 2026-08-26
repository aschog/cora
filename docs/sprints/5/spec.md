# Sprint 5 — the capstone

The assignment (`assignment.md`) is open-ended: seven cases, and any alternative that
meets the criteria. cora is carried forward, not restarted. This file cuts the capstone
into stories with acceptance criteria and records which evaluation criterion each one
answers. Anything that maps to no story here is out of scope.

The sprint's shape comes from two places that agreed with each other: the reviewer's
write-up (`docs/sprints/4/review-feedback.md`) and the sprint-4 retrospective. Both said
the single agent should be a sequence of steps; both said the README does not convey the
idea. The tracked backlog is `sprint-5-feedback.md`.

## Purpose (criterion 1 · outcome quality)

**Case 1 and case 2, taken together.** cora is a document-grounded knowledge assistant
that works like an agent: point it at your own documents, ask in your own words, and it
decides what the turn needs — looking things up, running the domain's tools, remembering
you between sessions.

The domain is not in the agent. It comes from a plugin, and the shipped fitness coach is
the worked example, not the product.

**Target users:** people with a body of their own material and recurring questions over
it. What the capstone adds is not a new capability but a *finished* one — an answer you
can check, a store you can read, a number that says retrieval works, and a page that says
what happens to your data.

## Architecture decision (criterion 2 · learning application)

The agent stays on **LangGraph**, hexagonal, with the domain holding the state shape and
the engine holding the steps as plain functions. Two decisions are this sprint's:

- **The turn becomes a named sequence of steps, not one model loop.** Today `prepare →
  model ⇄ tools` is a ReAct loop where one model call decides everything; the reviewer's
  point is that a workflow of steps with one responsibility each is less fragile and
  easier to control. The model keeps the decisions that are genuinely its own — inside a
  step, not over the whole turn. Story 2.
- **One store for the raw text, not two.** Chroma keeps the embeddings; the cleaned text
  a citation opens onto moves from `adapters/sqlite_documents.py` to one Markdown file per
  source, behind the `Documents` port that already exists. Threads and remembered facts
  stay in SQLite — they are not duplicated raw data. Stories 3 and 4.

---

## Stories

Numbered in merge order. Each becomes an OpenSpec change under `openspec/changes/`, and
its text moves into that change's `proposal.md` when it is opened — this file then keeps
the heading and the link.

### 1. A reader learns what cora is for before anything else

As a person who lands on the repository,\
I want the first screen to tell me what problem this solves and for whom,\
so that I can decide whether it is for me without reading the code.

**Scenario:** the front door explains itself

- **Given** `README.md` as the front door
- **When** someone who has never seen cora reads its first screen
- **Then** they can say what problem it solves, who it is for and how it works
- **And** the showcase entry is linked near the top

Written day one, before the code — the retrospective names cutting it last as the cause of
the reviewer seeing it.

### 2. The turn is a workflow of named steps

As a developer of cora,\
I want a turn to run as a sequence of steps with one responsibility each,\
so that I can see where a turn is, control what each step may do, and test a step without
the whole loop.

**Scenario:** a question that needs documents

- **Given** a question that needs documents
- **When** the turn runs
- **Then** the trace names each step it took, in the order the workflow defines
- **And** a step's failure is contained and reported as that step's
- **And** the model's freedom is bounded to the step it serves

**Scenario:** a question that needs none

- **Given** a question that needs no documents
- **When** the turn runs
- **Then** it skips the steps that would have fetched them

### 3. The text behind a citation is a file I can open

As a user of cora,\
I want the text my answer cites to live in a readable file per source,\
so that I can open, inspect and delete it without a database.

**Scenario:** a citation opens onto a file

- **Given** a document is ingested
- **When** its cleaned text is kept
- **Then** one Markdown file per source holds it, and a citation opens onto that file
- **And** nothing duplicates the text a second time

### 4. A second domain has an obvious place to live

As a person setting cora up for their own field,\
I want to see where a second domain's documents and index go,\
so that adding one is a directory, not a redesign.

**Scenario:** two domains, side by side

- **Given** two domains configured
- **When** documents are added to each
- **Then** each domain's index and text sit under a place named for that domain
- **And** neither reads the other's
- **And** `README.md` states the layout in a paragraph

### 5. Retrieval has a number, not an impression

As a developer of cora,\
I want a set of questions with the sources that should answer them,\
so that a change to retrieval shows up as a number instead of a feeling.

**Scenario:** the evaluation set runs

- **Given** an evaluation set of 10–20 questions with their expected sources
- **When** it is run against an indexed corpus
- **Then** a report names how often the expected source was retrieved, and how often the
  answer cited it
- **And** a drop below the recorded threshold fails

### 6. What cora does with my data, said in one page

As a person uploading my own documents,\
I want one page saying what leaves my machine, what is stored and what the model is told,\
so that I can judge the privacy cost before I upload anything.

**Scenario:** the privacy and ethics page

- **Given** the docs site
- **When** a reader looks for the privacy and ethics page
- **Then** it names every place data goes — the model provider, the local index, the local
  text, remembered facts
- **And** it says what the injection screen does and does not catch, and where the answers
  can be wrong
- **And** the claims match what the code does

### 7. I can remove a document

As a user of cora,\
I want to remove a document I uploaded,\
so that an answer stops citing something I no longer want indexed.

**Scenario:** a document leaves

- **Given** an indexed document
- **When** I remove it
- **Then** its chunks leave the index, its text file is gone, and no later answer cites it
- **And** the list says how many chunks each source contributes

This is the tail: the story that drops first if the sprint runs short.

---

## Chores

Not stories — no failing test names them — but tracked, and each is a merge of its own.

- **The test suite, 20/80** — find the fifth of the 1,247 tests carrying most of the
  protection, extend only those, archive the rest under `tests/` and delete the archive
  after submission. Membership is decided by what would go undetected, not by count.
- **An architecture note for the frontend before story 7 touches it** — sprint 4 had none
  and said so in its retrospective.
- **The showcase entry**, uploaded before the review and kept current, with its link in
  `README.md` (story 1's criterion).

## Evaluation-criteria coverage

| Criterion | Where |
|---|---|
| 1 · Outcome quality | *Purpose* above; stories 2, 3, 7 make the working app checkable, and story 1 states what it is for |
| 2 · Learning application | *Architecture decision* above — LangGraph as a workflow, Chroma for embeddings, OpenRouter behind the `ChatModel` port, prompt rules as plugins; story 5 measures the retrieval half |
| 3 · Ethical considerations | Story 6, standing on sprint 4's injection screen and untrusted-document handling |
| 4 · Presentation | Stories 1, 2 and 5 supply the six points: the problem, the architecture, the data, the measurement, the hardest problem, what is next |
| 5 · Showcase submission | *Chores* — uploaded before the review, linked from `README.md` |

## Not in this sprint

Recorded with a reason, tracked in `sprint-5-feedback.md`.

- **Stronger injection rules and a scan of document text at ingest** — the screen is still
  two regexes. Defence in depth behind a fix that already holds by construction; story 6
  says what it does not catch rather than pretending it does.
- **The React page's heading outline and tab/panel wiring** — one coherent accessibility
  story, not a piece of it done off-list. Deferred, not dropped.
- **PostgreSQL + pgvector, second-stage reranking, richer chunk metadata** — deferred
  again. Story 3 changes where the *text* lives, not the index; the evaluation set from
  story 5 is what would justify the other two.

## Out of scope

- **A hosted deployment.** The assignment asks for the showcase entry and a README link,
  never a running URL; `make run` and `make run-react` are how it is demonstrated.
- **A second domain plugin.** Story 4 makes the *place* for one obvious; shipping one
  proves nothing the seam does not already.
- **Multi-modal input, code generation, parameter-tuning studies** — cases 4, 5 and 7 are
  not the case this project answers.
- **Authentication, multi-tenancy, cost dashboards.** cora runs on the machine of the
  person whose documents it holds.
