## MODIFIED Requirements

### Requirement: A part of the page that cannot be drawn is replaced by a sentence

Where a column or a panel throws while rendering, the page SHALL draw a sentence in its
place. The sentence SHALL name what could not be drawn, and SHALL replace nothing else.

#### Scenario: A panel that throws says so

- **GIVEN** a store answering with a shape the conversations panel cannot read
- **WHEN** the reader opens that panel
- **THEN** they are told that panel could not be drawn

#### Scenario: What threw is on the console

- **GIVEN** a part of the page that throws while rendering
- **WHEN** it is caught
- **THEN** the throw and the tree it came from reach the console


### Requirement: The conversation is reachable whatever the rail is showing

Where a conversation fixed to a field with a page is open, the conversations panel SHALL be
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

#### Scenario: Moving between panels

- **GIVEN** the rail showing a conversation
- **WHEN** the reader chooses another panel
- **THEN** that panel is drawn in its place, and the conversation is the one tab back

#### Scenario: A panel that cannot be drawn

- **GIVEN** a panel that throws while being drawn
- **WHEN** the reader looks at the rail
- **THEN** they are told that panel could not be drawn, and the page is still there


### Requirement: A conversation fixed to no page is drawn where it always was

A conversation fixed to a field with no page, or fixed to nothing, SHALL be drawn in the
middle of the screen, and the conversations panel SHALL be the list alone.

#### Scenario: Opening one that has no page

- **GIVEN** the rail chatting a conversation of a field with a page
- **WHEN** the reader opens one from the list that is fixed to nothing
- **THEN** the conversation is drawn in the middle and the rail is the list again

