# conversation Specification

## Purpose

A turn: one question in, one answer out, on a named thread that outlives the process
holding it. Everything else cora does happens inside a turn, so this is the capability
the others are read against.

## Requirements

### Requirement: A turn answers one question on a thread

The system SHALL answer a question against the thread it is asked on, and SHALL return
the answer together with the citations it rests on and the steps the turn took.

#### Scenario: A question is answered

- **WHEN** a question is asked on a thread
- **THEN** the answer, its citations and that turn's steps come back together

#### Scenario: A thread carries what was said before it

- **GIVEN** a thread that has already taken a turn
- **WHEN** a later question is asked on it
- **THEN** the model is given what was said before, and the answer may rest on it

### Requirement: A thread is the boundary between conversations

The system SHALL keep each thread's turns to itself, so nothing asked on one thread is
visible to another.

#### Scenario: Two conversations on one app

- **GIVEN** two threads on one running app
- **WHEN** a question is asked on each
- **THEN** neither answer rests on what the other thread holds

### Requirement: A finished turn is recorded and reopenable

The system SHALL record a turn once it has an answer, SHALL read a thread's turns back
oldest first, and SHALL list the threads that have answered something, newest first.

#### Scenario: A conversation is reopened

- **GIVEN** a thread whose turns were recorded
- **WHEN** the thread is read back
- **THEN** its turns come back in the order they were taken, each with what was asked,
  what was answered, and what that answer rested on

#### Scenario: A thread that answered nothing is in no list

- **GIVEN** a thread on which no turn has finished
- **WHEN** the conversations are listed
- **THEN** that thread does not appear

### Requirement: Recording is beside the answer, never a condition of it

The system SHALL answer a turn whether or not it has anywhere to record it.

#### Scenario: An app assembled with no conversation store

- **GIVEN** an app with no store for conversations
- **WHEN** a question is asked
- **THEN** it is answered, and nothing is kept

### Requirement: The model's tool rounds are bounded, per turn

The system SHALL cap how many rounds of tools one turn may spend, SHALL end a turn that
reaches the cap rather than looping, and SHALL give the next turn the whole budget
again.

#### Scenario: A turn spends its budget

- **GIVEN** a question whose answer keeps calling tools
- **WHEN** the turn reaches its round cap
- **THEN** the turn ends rather than continuing

#### Scenario: The next turn starts fresh

- **GIVEN** a turn that spent its whole budget
- **WHEN** the next question is asked on that thread
- **THEN** it may spend the full budget again
