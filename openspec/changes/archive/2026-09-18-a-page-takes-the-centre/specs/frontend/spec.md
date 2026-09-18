As a reader whose conversation is fixed to a field with a page,\
I want that page to be the screen and the conversation beside it,\
so that I work in the subject and can still ask cora about what I am doing.

## ADDED Requirements

### Requirement: A fixed field's page is what the screen is about

Where the conversation is fixed to a field that has a page, the page SHALL fill the
middle of the screen and the conversation SHALL move into the rail beside it. Where it
is fixed to a field with no page, or fixed to nothing, the screen SHALL be as it was.

#### Scenario: A field with a page is fixed to

- **GIVEN** a loaded plugin bringing the page of a field
- **WHEN** the reader fixes the conversation to that field
- **THEN** the page is drawn in the middle, and the conversation is in the rail

#### Scenario: One field is the field it is fixed to

- **GIVEN** a deployment offering one field, whose plugin brought a page
- **WHEN** the reader opens cora, having pinned nothing
- **THEN** the page is drawn, there being no other field the conversation could be in

#### Scenario: A field with no page

- **GIVEN** a loaded plugin registering a field and no page
- **WHEN** the reader fixes the conversation to it
- **THEN** the conversation is in the middle, as it is with nothing fixed

#### Scenario: Nothing is fixed to

- **GIVEN** a conversation answered in a field whose plugin brought a page
- **WHEN** the reader has fixed it to nothing
- **THEN** the conversation is in the middle, the page being what a fixed field brings

#### Scenario: The plugin goes while it is being read

- **GIVEN** a page drawn for a fixed field
- **WHEN** the plugin bringing it is deleted
- **THEN** the conversation returns to the middle without the reader reloading

### Requirement: The conversation is reachable whatever the rail is showing

The conversation in the rail SHALL NOT be one of the panels the tabs choose between. It
SHALL stay drawn as the reader moves between panels, as a turn moves the panels to the
steps, and where a panel cannot be drawn at all.

#### Scenario: Asking does not take the conversation away

- **GIVEN** a page drawn, and the conversation in the rail
- **WHEN** the reader asks something and the panels move to the steps
- **THEN** the conversation is still drawn, with what they typed and what came back

#### Scenario: Moving between panels

- **WHEN** the reader chooses another panel
- **THEN** that panel is drawn above the conversation, which is unchanged

#### Scenario: A panel that cannot be drawn

- **GIVEN** a panel that throws while being drawn
- **WHEN** the reader looks at the rail
- **THEN** they are told that panel could not be drawn, and the conversation is there

### Requirement: The conversation in the rail says which one it is

Drawn in the rail, under a list its own row is in, the conversation SHALL be headed by
the question that opened it, so the reader can tell it from the ones listed above.

#### Scenario: The open conversation is named

- **GIVEN** a page drawn, and a conversation that has been answered once
- **WHEN** the reader looks at the rail
- **THEN** the conversation is headed by the question it was opened with

#### Scenario: A conversation that has said nothing

- **GIVEN** a page drawn, and a conversation nothing has been asked in
- **WHEN** the reader looks at the rail
- **THEN** it is headed as the new one it is, and named by no question

### Requirement: The page can have the whole width

Folding the rail beside a page SHALL give the page the width the rail held. Unfolding it
SHALL bring the conversation back, with what was said still there.

#### Scenario: Folding for width

- **GIVEN** a page drawn with the conversation beside it
- **WHEN** the reader folds that rail
- **THEN** the page is drawn across the width, and the control that unfolds it remains

#### Scenario: Coming back to the conversation

- **WHEN** the reader unfolds the rail again
- **THEN** the conversation is drawn as they left it

### Requirement: A page is framed as the plugin's own

A page SHALL be framed so that it may use the camera, and SHALL NOT be framed as though
cora contained it — its reach being the trust the reader extended by loading the plugin.
The frame SHALL be named for the field it belongs to.

#### Scenario: The frame is named

- **GIVEN** a page drawn for a field
- **WHEN** the screen is read by name
- **THEN** the frame is named for that field

#### Scenario: A page asking for the camera

- **GIVEN** a page whose script asks for the camera
- **WHEN** it asks
- **THEN** the frame does not refuse it on cora's behalf
