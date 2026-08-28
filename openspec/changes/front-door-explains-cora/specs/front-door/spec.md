# A reader learns what cora is for before anything else

As a person who lands on the repository,\
I want the first screen to tell me what problem this solves and for whom,\
so that I can decide whether it is for me without reading the code.

## Purpose

What a reader is told before they read any code. The repository's first screen states the
problem cora solves, who it is for, how a turn works, what extending it involves and what
it deliberately does not have — so the decision to use it or walk away is made without
opening a module.

## ADDED Requirements

### Requirement: One sentence describes cora wherever cora is described

The project SHALL describe itself in one sentence, and every place that description is
repeated SHALL carry that same sentence: the front door, the docs site's front page and
its per-page description, the distribution metadata, and the briefing an agent reads.

#### Scenario: The sentence changes

- **GIVEN** the sentence stated on the front door
- **WHEN** it is rewritten
- **THEN** every other copy carries the new wording, and a copy left behind is a failure

#### Scenario: The description is more than the sentence

- **WHEN** the front door's opening paragraph is read
- **THEN** it opens with that sentence and continues past it, so the one-line description
  and the paragraph are not the same text

### Requirement: The front door states the problem, the reader and how it works

The front door SHALL state, before any installation instruction, what problem cora solves,
who it is for, and how a turn works — what the core does and what a plugin contributes.

#### Scenario: A stranger reads the first screen

- **GIVEN** someone who has never seen cora
- **WHEN** they read the front door before its quick start
- **THEN** they can say what problem it solves, who it is for, and how it works

### Requirement: The front door says what extending cora involves

The front door SHALL name what writing a plugin of one's own involves, and SHALL link the
how-to that walks through it.

#### Scenario: A reader who wants their own subject

- **GIVEN** a reader deciding whether cora can be pointed at their field
- **WHEN** they read the front door
- **THEN** they learn what a plugin contributes and where the how-to is, without opening
  the source

### Requirement: The front door names what cora does not have

The front door SHALL carry a block of what cora deliberately lacks, and each absence SHALL
state its reason beside it rather than after the list, so an absence reads as a decision
and not as a gap. The block SHALL name at least these four:

- **no sandbox around a plugin** — a plugin is code you chose to install, like any package
  you `uv add`, and saying so plainly is safer than a gate that implies a containment cora
  does not have
- **no registry to browse** — a named module and a folder are discovery; somewhere to find
  other people's plugins is a website, and there are no other people yet
- **no subject but the two shipped** — a subject *is* a plugin, so a third proves nothing
  the second did not
- **no goal that outlives a turn** — cora answers and stops; a task that accumulates is
  the next axis, not this one

#### Scenario: A reader looks for what is missing

- **WHEN** the block of absences is read
- **THEN** every item in it carries a reason, and no item is listed bare

### Requirement: The front door links the project's showcase entry

The front door SHALL link the project's showcase entry near the top, above the quick start.

#### Scenario: The entry is reachable from the first screen

- **WHEN** the front door's first screen is read
- **THEN** it carries a link to the showcase, and the link is not below the quick start
