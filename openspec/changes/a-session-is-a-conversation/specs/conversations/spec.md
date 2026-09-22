As a reader,\
I want the conversations I have had called conversations wherever cora names them,\
so that one word means one thing on the page, in the API and in the code I read.

## ADDED Requirements

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

## MODIFIED Requirements

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

