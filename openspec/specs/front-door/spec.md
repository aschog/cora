# front-door Specification

## Purpose

How cora introduces itself: one screen that says what it is for and carries the commands
that install it, run it and extend it. There is no documentation site — the front door
is the documentation.

## Requirements

### Requirement: The front door opens with what cora is for

The system SHALL open `README.md` with what problem cora solves and who it is for.

#### Scenario: A stranger reads the first screen

- **WHEN** someone who has never seen cora reads the first screen of `README.md`
- **THEN** they can say what problem it solves and who it is for

### Requirement: The front door carries the commands

The system SHALL state in `README.md` the commands that install cora, load its plugins,
run it, and run its gates, rather than linking a page that holds them. `README.md` SHALL
link no page under `docs/` that the repository does not carry.

#### Scenario: A reader installs and runs cora

- **WHEN** a reader reaches installing or running cora
- **THEN** `README.md` gives the commands themselves, and links no page for them

#### Scenario: Every link the front door makes resolves

- **WHEN** a reader follows a `docs/` link from `README.md`
- **THEN** the file it names is one the repository holds

### Requirement: The front door says what a plugin must export

The system SHALL state in `README.md` what a plugin must export, where it is dropped to
be loaded, and how its settings are named, and SHALL name the plugins under `plugins/`
as the worked examples rather than restating them.

#### Scenario: A reader writes their first plugin

- **WHEN** a reader reaches the subject of writing a plugin
- **THEN** `README.md` names `extend` as what it must export, `.cora/plugins/` as where
  it is dropped, and the `CORA_PLUGIN_<NAME>_<SETTING>` form its settings take
