As a reader,\
I want to delete a conversation from the list,\
so that one I mistyped or asked twice stops being part of what cora holds.

## Purpose

What cora keeps of a conversation once its turns are over, and what deleting one takes
with it: the record a reader comes back through, and the thread the model was answering
on.

## ADDED Requirements

### Requirement: A conversation can be deleted from the list

The system SHALL offer, for each conversation it lists, a way to delete that one. A
deleted conversation SHALL be gone from the list, and its turns SHALL no longer be
readable.

#### Scenario: A deleted conversation leaves the list

- **GIVEN** two conversations that have each answered a question
- **WHEN** one of them is deleted
- **THEN** the list holds the other one alone

#### Scenario: A deleted conversation's turns cannot be read back

- **GIVEN** a conversation with two recorded turns
- **WHEN** it is deleted
- **THEN** reading that conversation's turns finds none

### Requirement: Deleting a conversation deletes the thread it ran on

Deleting SHALL reach the state the turns were answered against, not the record alone.
The scope the conversation was pinned to, what the model was told, and any turn parked
mid-question SHALL go with it. One request SHALL settle both, so no conversation is
left half-deleted.

#### Scenario: The pin goes with the conversation

- **GIVEN** a conversation pinned to a field
- **WHEN** it is deleted
- **THEN** that thread holds no pin

#### Scenario: A conversation parked mid-question cannot be picked up

- **GIVEN** a conversation whose turn stopped to ask the reader something
- **WHEN** it is deleted
- **THEN** resuming that thread is refused, as it is for a thread waiting on nothing

### Requirement: A conversation in use is not deletable

The system SHALL offer no way to delete the conversation open on the page, nor one it is
still answering a question in. A reader leaves the first, and waits for the second: a
turn that landed after its conversation was deleted would record it back into the list.

#### Scenario: The open conversation offers no delete

- **GIVEN** a page reading one of two listed conversations
- **WHEN** the list is drawn
- **THEN** the open conversation offers no delete, and the other one does

#### Scenario: A conversation still being answered in offers no delete

- **GIVEN** a question asked in one conversation, and the reader now reading another
- **WHEN** the list is drawn while that question is still being answered
- **THEN** neither conversation offers a delete

### Requirement: Deleting what nothing holds is already done

Deleting a conversation no store holds SHALL succeed rather than fail. A deployment that
records no conversations at all SHALL answer the same way, having nothing to delete.

#### Scenario: A conversation nobody recorded

- **GIVEN** a thread nothing was ever recorded under
- **WHEN** it is deleted
- **THEN** the request succeeds and the list is unchanged

#### Scenario: A deployment that keeps no conversations

- **GIVEN** a cora assembled without a place to record turns
- **WHEN** a conversation is deleted
- **THEN** the request succeeds

### Requirement: A card left open in a deleted conversation is not returned to

A page holds on to the conversation a question was left open in, so a reload can find
the card again. Deleting that conversation SHALL let go of it, so no reload returns to a
conversation that is gone.

#### Scenario: A reload after deleting the parked conversation

- **GIVEN** a page that left a question open in a conversation, then deleted it
- **WHEN** the page is reloaded
- **THEN** it opens a new conversation rather than the deleted one's card
