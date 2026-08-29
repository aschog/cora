# front-door Specification

## Purpose

How cora introduces itself: one screen that says what it is for, and one sentence saying
what it is, written once and derived everywhere else.

## Requirements

### Requirement: The front door says what cora is for

The system SHALL open `README.md` with what problem it solves, who it is for and how a
turn works, above the quick start, and SHALL link the showcase entry near the top.

#### Scenario: A stranger reads the first screen

- **WHEN** someone who has never seen cora reads the first screen of `README.md`
- **THEN** they can say what problem it solves, who it is for and how it works
- **AND** the showcase entry is linked near the top

#### Scenario: What writing a plugin involves is linked, not repeated

- **WHEN** the front door reaches the subject of writing a plugin
- **THEN** it links `docs/how-to/write-a-plugin.md` rather than restating it

### Requirement: One sentence says what cora is, written once

The system SHALL hold the sentence describing it in `README.md` and nowhere else, and
every other place that shows it SHALL derive it from there rather than repeat it.

#### Scenario: The docs site shows the sentence it does not hold

- **WHEN** the site is built
- **THEN** its front page carries the paragraph included from `README.md`, and the
  description every page carries is read off that file at build time

#### Scenario: The sentence is changed in one place

- **WHEN** the sentence in `README.md` changes
- **THEN** nothing else has to be edited for the site to change with it, and the
  packaging summary is the one copy that is hand-kept, said so where it is written
