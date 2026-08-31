As a person using cora for one field at a time,\
I want the scope to decide what cora is and what it can reach,\
so that a fitness question is answered by a coach, and a travel tool cannot be picked by
mistake.

## Purpose

What focuses a turn on one field: the scope it runs under, how a conversation is pinned
to one for good, and how cora reads a question when nothing is pinned.

## ADDED Requirements

### Requirement: A pinned conversation runs in its scope and no other

The system SHALL run every turn of a pinned conversation under that scope alone, beside
what is system-wide. It SHALL offer the model no tool belonging to another scope, and
SHALL state no other scope's instructions.

#### Scenario: The pin decides what the model is told

- **GIVEN** two scopes are loaded and a conversation pinned to one
- **WHEN** anything is asked
- **THEN** only that scope's instructions are in the brief, beside the system-wide ones

#### Scenario: Another scope's tools are not offered

- **GIVEN** the same conversation
- **WHEN** the model is called
- **THEN** the other scope's tools are absent from what it may call

### Requirement: A pin belongs to the conversation and is set once

The system SHALL keep a conversation's pin in the conversation's own state, and SHALL
apply it to every turn after the one that set it. It SHALL refuse a pin to a second
scope, naming the scope the conversation is already in.

#### Scenario: A conversation is pinned mid-flight

- **GIVEN** an unpinned conversation that has turned out to be about one field
- **WHEN** that scope is pinned
- **THEN** every later turn runs under it

#### Scenario: A question that was refused pins nothing

- **GIVEN** a question a rule refuses, sent with a scope to pin
- **WHEN** it is refused
- **THEN** the conversation is pinned to nothing, and another scope may still be pinned

#### Scenario: A second field is refused

- **GIVEN** a conversation pinned to one scope
- **WHEN** a second scope is pinned to it
- **THEN** it is refused, and the refusal names the scope already pinned

#### Scenario: The pin outlives the page

- **GIVEN** a pinned conversation
- **WHEN** it is reopened in a new page
- **THEN** it reports the same scope, read from the conversation's own state

#### Scenario: The pin binds what comes next, not what came before

- **GIVEN** turns that ran unpinned, before the pin
- **WHEN** the conversation is reopened
- **THEN** they read as they ran, and nothing is answered again under the pin

### Requirement: An unpinned turn is routed, every turn

The system SHALL read an unpinned question and run the turn under the scope it names.
It SHALL report which scope it routed to, and SHALL route the next question afresh —
so one unpinned conversation may answer a turn in each scope.

#### Scenario: The turn runs where it was routed

- **GIVEN** two scopes loaded and none pinned
- **WHEN** a question belonging to one is asked
- **THEN** the turn runs under that scope, and its steps name the scope chosen

#### Scenario: The next question is read on its own

- **GIVEN** the same conversation, having answered in one scope
- **WHEN** a question belonging to the other is asked
- **THEN** that turn runs under the other scope

#### Scenario: Routing is wired into the turn

- **GIVEN** a scripted model that names a scope
- **WHEN** the turn runs
- **THEN** it runs under that scope, and the steps say so, with no model called

### Requirement: A question fitting two scopes is put to the user

The system SHALL stop the turn and ask which scope was meant, rather than choosing one.
It SHALL then answer under the scope the user chose.

#### Scenario: cora asks rather than guessing

- **GIVEN** a question that fits both loaded scopes
- **WHEN** the turn runs
- **THEN** cora asks which was meant, and answers under the one chosen

#### Scenario: The scope chosen is the scope answered in

- **GIVEN** the same question, and a second reading of it that would name one scope
- **WHEN** the turn is resumed on the reader's choice
- **THEN** it runs under what they chose, and the trace says it was chosen

### Requirement: A question fitting no scope is answered plainly

The system SHALL answer a question belonging to no loaded scope under a default scope of
its own, with only the system-wide instructions and tools. It SHALL report that it did.

#### Scenario: The default scope answers

- **GIVEN** two scopes loaded and a question belonging to neither
- **WHEN** the turn runs
- **THEN** it is answered with the system-wide instructions and tools alone

#### Scenario: The default scope is named

- **WHEN** that turn's steps are read
- **THEN** they name the default scope as the one it ran under

### Requirement: cora ships a second field to route between

The system SHALL ship a travel plugin registering instructions and documents under its
own scope. It SHALL register no tool of its own yet, so routing has a second field
without a second set of things to call.

#### Scenario: Travel is a scope of its own

- **GIVEN** the travel plugin as it is shipped
- **WHEN** its registrations are read
- **THEN** its instructions carry its own scope, and nothing is system-wide

#### Scenario: The travel corpus is cora's to search

- **GIVEN** the travel plugin loaded
- **WHEN** a travel question is answered
- **THEN** the passages cited come from that plugin's own documents

### Requirement: Routing is measured against a recorded set

The system SHALL hold a recorded set of questions, each with the scope it belongs to,
covering questions asked alone and questions asked as follow-ups. Run against a real
model, it SHALL report how often the router chose the right scope, and SHALL fail when
that share falls below the recorded threshold.

#### Scenario: The report names the share

- **GIVEN** the recorded set and a real model
- **WHEN** the router is run over it
- **THEN** a report names how often the right scope was chosen

#### Scenario: A drop below the threshold fails

- **GIVEN** a run whose share is under the recorded threshold
- **WHEN** the report is read
- **THEN** that tier fails
