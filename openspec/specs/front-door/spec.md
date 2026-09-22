# front-door Specification

## Purpose

How cora introduces itself: one screen that says what it is for, and carries the
commands that install it, run it and extend it. There is no documentation site — the
front door is the documentation.

## Requirements

### Requirement: The front door says what cora is for

The system SHALL open `README.md` with what problem cora solves and who it is for, and
SHALL link the showcase entry near the top.

#### Scenario: A stranger reads the first screen

- **WHEN** someone who has never seen cora reads the first screen of `README.md`
- **THEN** they can say what problem it solves and who it is for
- **AND** the showcase entry is linked near the top

### Requirement: The front door carries the commands

The system SHALL state in `README.md` the commands that install cora, load its plugins,
run it, and run its gates, rather than linking a page that holds them. No page holds
them: `README.md` is where they live.

#### Scenario: A reader installs and runs cora

- **WHEN** a reader reaches installing or running cora
- **THEN** `README.md` gives the commands themselves

#### Scenario: A reader writes a plugin

- **WHEN** a reader reaches the subject of writing a plugin
- **THEN** `README.md` states what a plugin must export and where it is dropped, and
  names the shipped plugins under `plugins/` as the worked examples
