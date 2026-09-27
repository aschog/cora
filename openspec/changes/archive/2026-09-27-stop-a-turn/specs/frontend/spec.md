As a reader watching cora work,\
I want to stop a turn that is taking too long,\
so that I get the conversation back without waiting for an answer I no longer want.

## ADDED Requirements

### Requirement: A turn that is running can be stopped

While a turn runs, the composer's ask control SHALL be a stop control, and taking it
SHALL end that turn. The control SHALL be the same one, because a reader cannot ask and
stop at once. A conversation with no turn running SHALL offer no way to stop one.

#### Scenario: The control says what it does now

- **GIVEN** a question has been asked and cora is working
- **WHEN** the composer is read
- **THEN** its control stops the turn rather than asks one

#### Scenario: The turn ends when it is taken

- **GIVEN** cora is working on a turn
- **WHEN** the reader stops it
- **THEN** the composer takes a question again

#### Scenario: Nothing to stop

- **GIVEN** a conversation with no turn running
- **WHEN** the composer is read
- **THEN** its control asks a question

### Requirement: A stopped turn says the reader stopped it

A stopped turn SHALL leave its question on the page under a sentence saying the reader
stopped it. It SHALL leave no answer, whole or part, because a stopped turn is recorded
nowhere and nothing brings one back. The conversation SHALL take the next question as
it always did.

#### Scenario: The question stays under a sentence

- **GIVEN** cora has written half an answer
- **WHEN** the reader stops the turn
- **THEN** the question stands with a sentence saying they stopped it, and no answer

#### Scenario: A stopped turn is not recorded

- **GIVEN** a turn the reader stopped
- **WHEN** the conversation is read back from the store
- **THEN** that turn is not among its turns

### Requirement: A turn nobody is reading is stopped

Where the reader is no longer reading a turn, cora SHALL stop walking it. This SHALL
hold however the reading ended — the turn stopped, the page closed, the connection
lost. The turn SHALL end at the next step it takes or the next prose it writes,
whichever comes first.

#### Scenario: The model is not asked again

- **GIVEN** a turn whose first round called a tool
- **WHEN** the reader stops before the second round
- **THEN** the model is not asked for that round

#### Scenario: A closed page stops the turn too

- **GIVEN** a turn being streamed to a page
- **WHEN** the page goes away without stopping it
- **THEN** the turn stops as though it had been stopped
