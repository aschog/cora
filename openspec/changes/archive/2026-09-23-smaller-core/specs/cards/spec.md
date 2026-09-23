## MODIFIED Requirements

### Requirement: Cora asks for values it does not hold

The `ask` plugin SHALL let a turn stop and ask the reader for named values it does not
hold and cannot look up. The ask SHALL name two values or more, and SHALL reach the
reader as one card of them. An ask of a single value SHALL be refused, and the model
SHALL be told to ask for it in prose. A cora that has not loaded the plugin SHALL offer
no tool that asks.

#### Scenario: Four values are asked as one card

- **GIVEN** a turn whose answer needs a route, two dates and a budget
- **WHEN** cora asks the reader for them
- **THEN** one card stands with a field for each, under a prompt saying what it is for

#### Scenario: One value is asked in the answer

- **GIVEN** a turn whose answer needs only a height nobody has written down
- **WHEN** cora asks for it
- **THEN** no card stands, and the answer asks for the height in a sentence

#### Scenario: A bare cora can ask

- **GIVEN** a cora with the ask plugin loaded and nothing else
- **WHEN** the tools it offers are listed
- **THEN** one of them asks the reader for values, beside the one that settles a fact

#### Scenario: Without the plugin nothing asks

- **GIVEN** a cora with no plugin loaded
- **WHEN** the tools it offers are listed
- **THEN** nothing among them stops the turn to ask

#### Scenario: A field says what kind of value it is

- **GIVEN** cora asks for a day, a whole number, and one of three named choices
- **WHEN** the card is drawn
- **THEN** the reader is offered a date control, a number control, and those three

### Requirement: A form may be raised again where a fork may not

A conversation SHALL put one fork between remembered values once, and the same fork
asked again SHALL be refused. A form SHALL be raised as often as the round budget
allows, where two values or more are still missing: a reader who skipped those boxes
left a gap cora cannot fill from anywhere else. Where one box is all that is still
missing, cora SHALL ask for it in prose. Every ask SHALL cost the round it was made in,
and a round asking twice SHALL put each card on its own.

#### Scenario: A second fork is refused

- **GIVEN** a conversation that has already put a fork between two remembered values
- **WHEN** it asks the same fork a second time
- **THEN** the ask is refused, the reader is not stopped again, and the turn answers

#### Scenario: A form after a filled form still reaches the reader

- **GIVEN** a turn whose form came back with two required values skipped
- **WHEN** cora asks for what is still missing
- **THEN** a second card stands, and the reader is not asked for them in prose

#### Scenario: One value still missing is asked in the answer

- **GIVEN** a turn whose form came back with one required value skipped
- **WHEN** cora asks for what is still missing
- **THEN** no second card stands, and the answer asks for that value

#### Scenario: A round that asks both ways puts the one still open

- **GIVEN** a round asking for a fork already settled this conversation, and for values
- **WHEN** the turn reaches the gate
- **THEN** the fork is refused, the reader is put the form alone, and the round runs on

## ADDED Requirements

### Requirement: A card says where the reader's action lands

A card put ahead of a tool call MAY name one argument of the call, and the action the
reader takes SHALL then be written into that argument before the tool runs. A card
naming none SHALL settle on the action alone, as it does today. The way out of such a
card SHALL be an action like the others, so the tool runs and says in its own words
that nothing was chosen.

#### Scenario: The option taken reaches the tool

- **GIVEN** a tool whose card offers three options and names the argument they land in
- **WHEN** the reader takes the second
- **THEN** the tool runs with the second option's value in that argument

#### Scenario: The way out reaches the tool too

- **GIVEN** that card
- **WHEN** the reader takes the way out
- **THEN** the tool runs, and the model is told nothing was chosen in the tool's words

#### Scenario: A card naming no argument is unchanged

- **GIVEN** a tool whose card names no argument
- **WHEN** the reader confirms it
- **THEN** the tool runs on the arguments the model wrote
