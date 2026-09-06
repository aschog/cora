As a reader,\
I want the conversation I am reading to have an address of its own,\
so that I can link to it, reload back into it, and press back out of it.

## Purpose

The address a conversation is reached by, and what the page does when it changes. A
conversation is a thing you can return to rather than a state the page happens to be in.

## ADDED Requirements

### Requirement: The conversation being read is named in the address

The page SHALL write the conversation it is showing into the address, once it is drawn.
A conversation that could not be read SHALL NOT be named there.

#### Scenario: Opening a conversation names it

- **GIVEN** a conversation listed under SESSIONS
- **WHEN** the reader opens it
- **THEN** the address names that conversation

#### Scenario: A conversation that would not open is not named

- **GIVEN** a conversation whose turns cannot be read
- **WHEN** the reader opens it
- **THEN** the page says so, and the address names no conversation

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

- **GIVEN** a conversation opened from SESSIONS
- **WHEN** the address the page wrote for it is read back
- **THEN** its turns are read once

### Requirement: Starting over takes the conversation out of the address

Leaving a conversation SHALL clear the address, because the conversation replacing it is
in no store and has nothing to link to.

#### Scenario: A new conversation is nameless

- **GIVEN** a reader in a conversation the address names
- **WHEN** they start a new one
- **THEN** the address names no conversation, and its turns are gone from the page

### Requirement: A card left open outranks the address

Where a card was left open in one conversation and the address names another, the page
SHALL open in the conversation holding the card.

#### Scenario: The card is what the page comes back to

- **GIVEN** a card left open in a conversation listed under no session
- **AND** an address naming a different, recorded conversation
- **WHEN** the page is drawn
- **THEN** the card is what the reader is shown

### Requirement: An address that could mean another path names no conversation

The page SHALL refuse a thread from the address that is not made of letters, digits and
dashes, and SHALL escape every thread it puts into the path of a request.

#### Scenario: A path climbed out of is refused

- **GIVEN** an address whose thread decodes to `../memory`
- **WHEN** the page reads it
- **THEN** it names no conversation, and no request is made for it

#### Scenario: A thread this page minted is read back

- **GIVEN** an address naming a thread of letters, digits and dashes
- **WHEN** the page reads it
- **THEN** that thread is the conversation it opens
