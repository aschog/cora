As a reader,\
I want a row I have confirmed away to leave its list when I say so,\
so that the click does not read as having missed.

## Purpose

When a deleted conversation leaves the list, and what the page does when the store
refuses. The reader has already answered a question about it, so the list follows the
answer rather than the round trip.

## ADDED Requirements

### Requirement: A conversation leaves the list when the reader confirms it

The list SHALL stop showing a conversation as soon as the reader confirms deleting it,
before the store has answered.

#### Scenario: The row goes before the store answers

- **GIVEN** a conversation the reader has confirmed deleting
- **WHEN** the store has not yet answered
- **THEN** the list no longer shows it, and shows the others

### Requirement: A conversation the store would not delete comes back, with the reason

Where the store refuses the delete, the conversation SHALL be listed again and the page
SHALL say why. A row reappearing is never the only account of what happened.

#### Scenario: Refused, so it is listed again

- **GIVEN** a conversation the reader confirmed deleting
- **WHEN** the store refuses
- **THEN** it is listed again, and the page says why

### Requirement: What went through is confirmed by the store

After a delete, the page SHALL read the listing again rather than keep its own account of
what changed.

#### Scenario: The list is read again either way

- **GIVEN** a delete the reader confirmed
- **WHEN** the store has answered, however it answered
- **THEN** the list the reader is shown is the one the store gave
