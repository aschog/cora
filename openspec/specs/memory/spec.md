# memory Specification

## Purpose

What cora keeps about the person it is talking to, across every thread and every
session: facts they told it, offered back to the model as what it already knows.

## Requirements

### Requirement: A fact told to cora outlives the session

The system SHALL keep a fact it is told about the user, and SHALL still hold it in a
later session.

#### Scenario: A fact shared last session briefs the model

- **GIVEN** a fact remembered in an earlier session
- **WHEN** a question is asked in a new one
- **THEN** the model is briefed with that fact before it answers

### Requirement: Remembered facts are system-wide, not a thread's

The system SHALL make what it remembers about the user available on every thread.

#### Scenario: A fact learned on one thread is known on another

- **GIVEN** a fact remembered while answering on one thread
- **WHEN** a question is asked on a different thread
- **THEN** the model is briefed with that fact there too

### Requirement: A fact can be forgotten, one at a time

The system SHALL name each fact by a key that does not change for its life, SHALL forget
the fact that key names and no other, and SHALL treat forgetting an unheld key as no
error.

#### Scenario: Clearing what is remembered

- **GIVEN** facts that have been remembered
- **WHEN** they are forgotten
- **THEN** the store is empty and the next brief mentions none of them

### Requirement: Remembering is optional, and its absence is silent

The system SHALL run without a memory, and SHALL then neither offer the model a way to
remember nor tell it to.

#### Scenario: An app assembled with no memory

- **GIVEN** an app with no memory
- **WHEN** a question is asked
- **THEN** it is answered, nothing is remembered, and the brief names no remembering

### Requirement: A memory that cannot be read does not cost the turn

The system SHALL answer the turn when what is remembered cannot be read, and SHALL say
in that turn's steps that it went unread.

#### Scenario: The store is unreachable

- **GIVEN** a memory that fails to be read
- **WHEN** a question is asked
- **THEN** the turn is answered without it, and its steps record that memory was unread
