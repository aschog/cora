# front-door Specification

## Purpose

How cora introduces itself: one screen that says what it is for and links everything
else, a site that states its own description, and a test over the names the pages claim.

## Requirements

### Requirement: The front door says what cora is for

The system SHALL open `README.md` with what problem cora solves and who it is for, SHALL
link the showcase entry near the top, and SHALL carry no instruction a page of its own
holds — installing it, running it, loading a plugin, or writing one. Every such subject
SHALL be a link.

#### Scenario: A stranger reads the first screen

- **WHEN** someone who has never seen cora reads the first screen of `README.md`
- **THEN** they can say what problem it solves and who it is for
- **AND** the showcase entry is linked near the top

#### Scenario: What writing a plugin involves is linked, not repeated

- **WHEN** the front door reaches the subject of writing a plugin
- **THEN** it links `docs/how-to/write-a-plugin.md` rather than restating it

#### Scenario: Running it is linked, not repeated

- **WHEN** the front door reaches installing or running cora
- **THEN** it links the page that holds the commands, and states none itself

### Requirement: The site describes itself

The docs site SHALL state the description every page carries, and no build step SHALL
read `README.md`. Where two pages would state the same fact about what cora does, one
SHALL state it and the other SHALL link that one.

#### Scenario: The docs site describes itself

- **WHEN** the site is built
- **THEN** every page carries a description the site states, and no build step reads
  `README.md`

#### Scenario: A fact has one home

- **WHEN** two pages would state the same fact about what cora does
- **THEN** one of them states it and the other links that one

### Requirement: What the docs name, cora has

A test SHALL fail when a documentation page names a `CORA_*` variable no configuration
reads, or a `make` target the `Makefile` does not define.

#### Scenario: A page names a variable nothing reads

- **GIVEN** a documentation page naming `CORA_PLUGIN_FITNESS_UNITS`
- **WHEN** the guards run
- **THEN** the test fails, naming the page and the variable

#### Scenario: A page names a target that exists

- **GIVEN** the pages as they stand
- **WHEN** the guards run
- **THEN** every `make` target and every `CORA_*` name they carry is one the repository
  has
