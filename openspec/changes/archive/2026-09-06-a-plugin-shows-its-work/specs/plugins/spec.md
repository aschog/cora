As a plugin author,\
I want the work my plugin does itself to appear on the trace,\
so that a reader can follow a turn my code took part in.

## Purpose

What a plugin may put on the trace, and where it lands. A plugin that runs a loop of its
own is read back rather than guessed at, the same way the rest of a turn is.

## ADDED Requirements

### Requirement: A plugin says what it did, and the reader reads it

A plugin SHALL be able to contribute one line saying what it just did, with detail
behind it for a reader who opens it. The line SHALL name the plugin that took it.

#### Scenario: A plugin's own work is on the trace

- **GIVEN** a plugin whose tool says what it did while the call runs
- **WHEN** the turn is answered
- **THEN** the trace carries that line, naming the plugin

#### Scenario: The detail is behind the line

- **GIVEN** a plugin that says what it did and gives detail with it
- **WHEN** the reader opens that step
- **THEN** the detail it gave is what they read

### Requirement: What a plugin shows lands under the call it happened in

A line a plugin contributes during a tool call SHALL appear among that call's own steps,
beside the rounds a delegated loop reports there.

#### Scenario: Shown under the call, not beside it

- **GIVEN** a plugin whose tool shows two lines and delegates a loop once
- **WHEN** the turn is answered
- **THEN** all three stand under that one call, and none beside it

#### Scenario: Shown outside a call is dropped

- **GIVEN** a plugin that shows a line while it is being loaded
- **WHEN** a turn is answered afterwards
- **THEN** the trace carries no such line, and loading the plugin did not fail

### Requirement: A plugin cannot sign another plugin's name

The name on the line SHALL be the name cora loaded that plugin under, whatever the
plugin passes.

#### Scenario: A plugin names itself something else

- **GIVEN** a plugin that tries to show a line under another plugin's name
- **WHEN** the turn is answered
- **THEN** the line names the plugin that showed it

### Requirement: A plugin may show that something went wrong

A plugin SHALL be able to mark what it shows as having failed, and the trace SHALL show
it as a failed step without ending the turn.

#### Scenario: A failed line is shown as failed

- **GIVEN** a plugin whose loop shows a line marked as gone wrong
- **WHEN** the turn is answered
- **THEN** that step reads as failed and the turn still answers
