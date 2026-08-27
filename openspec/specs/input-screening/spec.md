# input-screening Specification

## Purpose

What cora refuses before a turn starts. A screened question costs the thread nothing:
the rules run before the transcript is written and before any model is called, and what
they say is written for the user to read.

## Requirements

### Requirement: Input is screened before any model call

The system SHALL run its rules over a question before the turn writes anything or calls
the model, and SHALL leave the thread untouched when a rule refuses.

#### Scenario: A refused question costs the thread nothing

- **GIVEN** a question a rule refuses
- **WHEN** it is asked
- **THEN** no model is called, nothing is written to the thread, and the refusal names
  what to do about it

### Requirement: cora screens what any input must be, whatever it was asked to be

The system SHALL refuse an empty question, and SHALL refuse one longer than the cap it
was assembled with, naming that cap.

#### Scenario: Nothing to answer

- **WHEN** an empty or blank question is asked
- **THEN** it is refused, asking for a question

#### Scenario: A whole document pasted as a question

- **WHEN** a question longer than the cap is asked
- **THEN** it is refused, and the refusal names the cap

### Requirement: A plugin may add rules of its own

The system SHALL run a plugin's rules after its own, and SHALL show the plugin's message
to the user when one refuses.

#### Scenario: A plugin refuses an input

- **GIVEN** a plugin bringing a rule
- **WHEN** an input that rule refuses is asked
- **THEN** the turn is refused before the model is called, with that rule's message

#### Scenario: cora's rules run first

- **GIVEN** an input cora would refuse outright
- **WHEN** a plugin rule is also loaded
- **THEN** cora's refusal is what happens, and the plugin's rule is never handed it

### Requirement: Screening for prompt injection is a plugin, not the core

The system SHALL leave injection screening to a plugin a deployment names, and SHALL
say that it starts with none.

#### Scenario: The screen is loaded

- **GIVEN** the prompt-safety plugin named to cora
- **WHEN** an injection attempt is asked
- **THEN** it is refused before the model is called

### Requirement: Retrieved text reaches the model marked as data, not instruction

The system SHALL hand retrieved excerpts to the model framed as untrusted document data
to be used as evidence only, so text a user uploaded cannot pose as an instruction from
the system.

#### Scenario: Retrieved passages carry the notice

- **GIVEN** a question answered from an indexed document
- **WHEN** the passages are handed to the model
- **THEN** they arrive marked as untrusted data, with instructions inside them named as
  something not to follow
