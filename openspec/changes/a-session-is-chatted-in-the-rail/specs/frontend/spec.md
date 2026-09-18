As someone training with the field's page on the screen,\
I want the rail to be the conversation I am in, with the others one click behind it,\
so that I can talk while I work and move between conversations without leaving the page.

## MODIFIED Requirements

### Requirement: The conversation is reachable whatever the rail is showing

Where a conversation fixed to a field with a page is open, the sessions panel SHALL be
that conversation's chat, filling the rail. It SHALL offer a way back to the list of
conversations, and opening one from that list SHALL make the rail its chat. A turn asked
there SHALL NOT move the panels to the steps, which would take the chat off the screen.

#### Scenario: Asking does not take the conversation away

- **GIVEN** a page drawn, and the rail showing its conversation
- **WHEN** the reader asks something
- **THEN** the conversation is still shown, with what they typed and what came back

#### Scenario: Back to the others

- **GIVEN** the rail showing a conversation
- **WHEN** the reader takes the way back
- **THEN** the list of conversations is shown in its place

#### Scenario: Into another one

- **GIVEN** the list of conversations shown
- **WHEN** the reader opens one that is fixed to a field with a page
- **THEN** the rail is that conversation's chat

#### Scenario: A panel that cannot be drawn

- **GIVEN** a panel that throws while being drawn
- **WHEN** the reader looks at the rail
- **THEN** they are told that panel could not be drawn, and the page is still there

## ADDED Requirements

### Requirement: A conversation chatted in the rail says which one it is

The chat SHALL be headed by the question that opened the conversation, the field it is
fixed to, and how many turns it holds.

#### Scenario: The head of an answered conversation

- **GIVEN** a conversation of two turns fixed to a field with a page
- **WHEN** it is chatted in the rail
- **THEN** its head carries the question it was opened with, that field, and its length

#### Scenario: A conversation that has said nothing

- **GIVEN** a conversation nothing has been asked in
- **WHEN** it is chatted in the rail
- **THEN** its head says it is a new one

### Requirement: A conversation that belongs to a field with a page is marked in the list

Every conversation in the list that is fixed to a field bringing a page SHALL carry a
mark the others do not, and the list SHALL say what the mark means.

#### Scenario: Marked and unmarked together

- **GIVEN** conversations fixed to a field with a page, and others fixed to nothing
- **WHEN** the list is read
- **THEN** the first carry the mark and the rest do not

#### Scenario: What the mark means

- **WHEN** the list holds a marked conversation
- **THEN** it says that such a conversation opens as a chat in this rail

### Requirement: A field is named once on the screen

Where a conversation chatted in the rail is headed by the field it is fixed to, the
strip that would say the same under it SHALL NOT be drawn. Where nothing else names the
field, that strip SHALL be drawn as it always was.

#### Scenario: Beside a page

- **GIVEN** a conversation chatted in the rail, headed by its field
- **WHEN** the reader looks at it
- **THEN** the field is named once, in that head

#### Scenario: In the middle

- **GIVEN** a conversation fixed to a field with no page
- **WHEN** the reader looks at it
- **THEN** the strip names the field, nothing else there doing so

### Requirement: A conversation fixed to no page is drawn where it always was

A conversation fixed to a field with no page, or fixed to nothing, SHALL be drawn in the
middle of the screen, and the sessions panel SHALL be the list alone.

#### Scenario: Opening one that has no page

- **GIVEN** the rail chatting a conversation of a field with a page
- **WHEN** the reader opens one from the list that is fixed to nothing
- **THEN** the conversation is drawn in the middle and the rail is the list again
