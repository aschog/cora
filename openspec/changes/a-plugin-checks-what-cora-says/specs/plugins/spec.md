As a plugin author,\
I want to see what cora is about to answer with,\
so that I can redact or rewrite it before the reader ever sees it.

## Purpose

The last point in a turn a plugin may take part in: the answer, settled and not yet
handed over. What leaves cora can be checked, the way what arrives already is.

## ADDED Requirements

### Requirement: A plugin sees the answer before the reader does

A plugin SHALL be able to subscribe to the answer being settled, and SHALL be given it
as text. What it hands back SHALL be what the reader is given, and handing back nothing
SHALL leave the answer as it was.

#### Scenario: An answer is redacted before it is handed over

- **GIVEN** a plugin subscribed to the answer, replacing a phone number with a marker
- **WHEN** a turn answers with a phone number in it
- **THEN** the reader is given the answer with the marker, and the number is nowhere in it

#### Scenario: A handler that changes nothing changes nothing

- **GIVEN** a plugin subscribed to the answer that hands back nothing
- **WHEN** a turn answers
- **THEN** the reader is given the answer exactly as the model wrote it

### Requirement: Amendments to the answer chain in load order

Each subscribed handler SHALL be given what the one before it returned, so two plugins
both change the answer and neither undoes the other.

#### Scenario: Two plugins each change the answer

- **GIVEN** one plugin that redacts and a second that appends a notice, loaded in that order
- **WHEN** a turn answers
- **THEN** the reader is given an answer that is both redacted and carries the notice

### Requirement: A broken check costs the turn nothing

A handler that raises, or that hands back something that is not text, SHALL be dropped
and the turn SHALL still answer.

#### Scenario: A handler raises

- **GIVEN** a plugin subscribed to the answer whose handler raises
- **WHEN** a turn answers
- **THEN** the reader is given the answer, and the trace says that plugin could not change it

#### Scenario: A handler hands back something that is not text

- **GIVEN** a plugin subscribed to the answer that hands back a number
- **WHEN** a turn answers
- **THEN** the answer stands unchanged and the trace records the failure

### Requirement: The citations follow the answer that was amended

Citations SHALL be read off the answer as it was amended. A claim removed by a handler
SHALL take its citation with it.

#### Scenario: A redacted sentence drops its citation

- **GIVEN** an answer citing two passages, and a plugin that removes the sentence carrying the second
- **WHEN** the turn is answered
- **THEN** the reader is given one citation, and it is the one still cited

### Requirement: The trace names the plugin that changed the answer

A handler that changes the answer SHALL appear on the trace, named for its plugin, as a
handler at any other point does.

#### Scenario: A reader sees who changed it

- **GIVEN** a plugin that redacted the answer
- **WHEN** the reader opens the trace
- **THEN** a step names that plugin and says it changed the answer
