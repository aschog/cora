# citations Specification

## Purpose

What an answer rests on, said in a way the reader can check: a passage becomes a
numbered `[n]` in the answer, and that number opens onto the text it came from.

## Requirements

### Requirement: An answer names the passages it rests on

The system SHALL number the passages a turn was given, SHALL let the answer refer to
them as `[n]`, and SHALL return those citations beside the answer.

#### Scenario: An answer from a document cites it

- **GIVEN** an indexed document holding the answer
- **WHEN** a question about it is asked
- **THEN** the answer carries `[n]` markers, and the citations behind them come back
  with it

### Requirement: A number keeps its passage for the life of the conversation

The system SHALL hand a passage its number once, and SHALL never move a number a reader
has seen to a different passage.

#### Scenario: A source found again keeps its number

- **GIVEN** a passage cited as `[1]` in an earlier turn
- **WHEN** a later turn retrieves the same passage
- **THEN** it is `[1]` again

#### Scenario: An answer echoing an earlier number resolves to that source

- **GIVEN** a conversation in which `[1]` was handed out
- **WHEN** a later answer writes `[1]`
- **THEN** it resolves to the passage that number was given to

### Requirement: A citation opens onto the text it was cut from

The system SHALL carry, with each citation, the document to show and the span to read,
so the cited passage can be opened rather than only named.

#### Scenario: A cited passage is opened

- **GIVEN** an answer citing `[1]`
- **WHEN** that citation is opened
- **THEN** the passage it names is shown in the text it was cut from

### Requirement: Two passages of one document are two citations

The system SHALL treat each passage as its own citation, and SHALL keep a number bound
to its passage even when the same filename is uploaded again with other text in it.

#### Scenario: One document, two cited passages

- **GIVEN** a document two of whose passages were cited
- **WHEN** the citations are read
- **THEN** they are two, each with its own number and span
