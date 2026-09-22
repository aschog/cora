# conversations Specification

## Purpose

What cora keeps of a conversation once its turns are over, and what deleting one takes
with it: the record a reader comes back through, and the thread the model was answering
on.

## Requirements

### Requirement: A conversation can be deleted from the list

The system SHALL offer, for each conversation it lists, a way to delete that one, named
for the conversation it would delete. A deleted conversation SHALL be gone from the
list, and its turns SHALL no longer be readable.

#### Scenario: A deleted conversation leaves the list

- **GIVEN** two conversations that have each answered a question
- **WHEN** one of them is deleted
- **THEN** the list holds the other one alone

#### Scenario: A deleted conversation's turns cannot be read back

- **GIVEN** a conversation with two recorded turns
- **WHEN** it is deleted
- **THEN** reading that conversation's turns finds none

#### Scenario: Each control says which conversation it deletes

- **GIVEN** two listed conversations
- **WHEN** the list is drawn
- **THEN** each delete control is named for the conversation it would delete

### Requirement: Deleting a conversation is asked about first

Deleting SHALL be confirmed before it happens. The system SHALL put the question over
the page, naming the conversation and saying what is lost and what is not. Nothing SHALL
be deleted until it is confirmed, and keeping the conversation SHALL leave it exactly as
it was.

#### Scenario: The control asks rather than deletes

- **GIVEN** a listed conversation the reader has left
- **WHEN** its delete control is used
- **THEN** the reader is asked, and nothing has been deleted

#### Scenario: The question says what is lost

- **GIVEN** that question open
- **WHEN** it is read
- **THEN** it names the conversation, and says the documents and the memory are untouched

#### Scenario: A confirmed delete happens

- **GIVEN** that question open
- **WHEN** it is confirmed
- **THEN** the conversation is deleted and gone from the list

#### Scenario: Keeping the conversation deletes nothing

- **GIVEN** that question open
- **WHEN** the reader keeps the conversation instead
- **THEN** nothing is deleted, and it is still listed

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

### Requirement: The conversation being read is named in the address

The page SHALL write the conversation it is showing into the address, once it is drawn.
A conversation that could not be read SHALL NOT be named there.

#### Scenario: Opening a conversation names it

- **GIVEN** a conversation listed under CONVERSATIONS
- **WHEN** the reader opens it
- **THEN** the address names that conversation

#### Scenario: A conversation that would not open is not named

- **GIVEN** a conversation whose turns cannot be read
- **WHEN** the reader opens it
- **THEN** the page says so, and the address does not name it

### Requirement: A conversation is named once it has answered, not before

A conversation the reader started SHALL be named in the address when its first turn
lands. Until then it is in no store, and there is nothing to name.

#### Scenario: A fresh conversation is unnamed

- **GIVEN** a page opened with no conversation in the address
- **WHEN** the reader has asked nothing
- **THEN** the address names no conversation

#### Scenario: The first answer names it

- **GIVEN** a conversation the reader started
- **WHEN** its first question is answered
- **THEN** the address names that conversation

#### Scenario: Naming it does not take the reader anywhere

- **GIVEN** a turn answered in a conversation the reader has since left
- **WHEN** it lands
- **THEN** the address still names the conversation they are in

### Requirement: A page opened at an address opens in what it names

The page SHALL read the address when it is drawn, and open in the conversation named
there.

#### Scenario: A link opens the conversation it points at

- **GIVEN** an address naming a recorded conversation
- **WHEN** the page is opened at it
- **THEN** that conversation's turns are what the reader is shown

### Requirement: The address changing under the page is a request

The page SHALL open the conversation the address names when the address changes beneath
it. An address the page itself just wrote SHALL NOT be read back as a request.

#### Scenario: Back returns to the conversation before

- **GIVEN** a reader who has opened one conversation and then another
- **WHEN** the address returns to the first
- **THEN** the first conversation is what they are shown

#### Scenario: Opening one does not open it twice

- **GIVEN** a conversation opened from CONVERSATIONS
- **WHEN** the address the page wrote for it is read back
- **THEN** its turns are read once

### Requirement: Starting over takes the conversation out of the address

Leaving a conversation SHALL clear the address. The conversation replacing it is in no
store, and has nothing to link to.

#### Scenario: A new conversation is nameless

- **GIVEN** a reader in a conversation the address names
- **WHEN** they start a new one
- **THEN** the address names no conversation, and its turns are gone from the page

### Requirement: A card left open outranks the address

Where a card was left open in one conversation, the page SHALL open there. It SHALL do
so though the address names another conversation.

#### Scenario: The card is what the page comes back to

- **GIVEN** a card left open in a conversation the list does not yet hold
- **AND** an address naming a different, recorded conversation
- **WHEN** the page is drawn
- **THEN** the card is what the reader is shown

### Requirement: An address that could mean another path names no conversation

The page SHALL refuse an address thread not made of letters, digits and dashes. It
SHALL escape every thread it puts into the path of a request.

#### Scenario: A path climbed out of is refused

- **GIVEN** an address whose thread decodes to `../memory`
- **WHEN** the page reads it
- **THEN** it names no conversation, and no request is made for it

#### Scenario: A thread this page minted is read back

- **GIVEN** an address naming a thread of letters, digits and dashes
- **WHEN** the page reads it
- **THEN** that thread is the conversation it opens

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

### Requirement: A conversation is called a conversation wherever the page names it

The page SHALL name a conversation as one in every label a reader meets. The tab over
the list SHALL read CONVERSATIONS. The control that starts one SHALL read "New
conversation". Refused, it SHALL say the reader is already in a new conversation. The
delete SHALL ask with "Delete conversation", and the way back from a chat SHALL read
"Back to other conversations". A notice about a turn landing elsewhere SHALL say it will
be listed under CONVERSATIONS. No label the reader meets SHALL call one a session.

#### Scenario: The tab

- **GIVEN** the rail
- **WHEN** its tabs are read
- **THEN** the one over the list reads CONVERSATIONS

#### Scenario: Starting one

- **GIVEN** a conversation the reader is in
- **WHEN** the control that starts another is read
- **THEN** it reads "New conversation"

#### Scenario: Already in a new one

- **GIVEN** a conversation nothing has been asked in
- **WHEN** the reader reaches for that control
- **THEN** it says they are already in a new conversation

#### Scenario: Deleting one

- **GIVEN** a listed conversation the reader has left
- **WHEN** its delete control is used
- **THEN** the question confirms with "Delete conversation"

#### Scenario: The way back

- **GIVEN** the rail chatting a conversation
- **WHEN** the way back is read
- **THEN** it reads "Back to other conversations"

#### Scenario: A turn landing elsewhere

- **GIVEN** a question still being answered in a conversation the reader left
- **WHEN** the page says so
- **THEN** it says the conversation will be listed under CONVERSATIONS

### Requirement: Conversations are reached at a path named for them

The API SHALL list every conversation that has answered at `/api/conversations`, newest
first. One conversation's turns, its pin, what it is parked on and its deletion SHALL be
served under that path. The path named for sessions SHALL answer nothing.

#### Scenario: Listed where they are named

- **GIVEN** a conversation that has answered once
- **WHEN** a client asks for `/api/conversations`
- **THEN** that conversation is listed, named by the question that opened it

#### Scenario: Read back from there

- **GIVEN** a listed conversation
- **WHEN** a client asks for its turns under `/api/conversations`
- **THEN** the turn it answered comes back

#### Scenario: The old path is gone

- **GIVEN** a running cora
- **WHEN** a client asks for `/api/sessions`
- **THEN** nothing is there
