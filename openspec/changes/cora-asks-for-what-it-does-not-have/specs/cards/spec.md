As someone cora is helping,\
I want to be asked for what it needs as one form,\
so that I fill it in once instead of answering a list of questions.

## ADDED Requirements

### Requirement: Cora asks for values it does not hold

Cora SHALL be able to stop a turn and ask the reader for named values it does not hold
and cannot look up. The ask SHALL reach the reader as one card of those values, and
SHALL be cora's own — available to a deployment that has loaded no plugin.

#### Scenario: Four values are asked as one card

- **GIVEN** a turn whose answer needs a route, two dates and a budget
- **WHEN** cora asks the reader for them
- **THEN** one card stands with a field for each, under a prompt saying what it is for

#### Scenario: A bare cora can ask

- **GIVEN** a cora with no plugin loaded
- **WHEN** the tools it offers are listed
- **THEN** one of them asks the reader for values, beside the one that settles a fact

#### Scenario: A field says what kind of value it is

- **GIVEN** cora asks for a day, a whole number, and one of three named choices
- **WHEN** the card is drawn
- **THEN** the reader is offered a date control, a number control, and those three

### Requirement: What the reader writes settles the ask

The values the reader writes SHALL reach the turn that asked, and the answer SHALL rest
on them. A reader who writes nothing SHALL settle the ask too: the turn SHALL carry on
without the values and SHALL say what it still needs.

#### Scenario: The turn answers on what was written

- **GIVEN** a turn stopped asking for a departure city
- **WHEN** the reader writes one and submits the card
- **THEN** the turn continues and its answer rests on that city

#### Scenario: Nothing written still settles it

- **GIVEN** a turn stopped asking for a departure city
- **WHEN** the reader takes the way out without writing one
- **THEN** the turn answers without it and says plainly what it still needs

#### Scenario: The trace carries the ask

- **GIVEN** a turn that stopped for values and was answered
- **WHEN** the trace is read
- **THEN** it says what was asked for and which fields came back filled

### Requirement: A form may be raised again where a fork may not

A turn SHALL put its fork between remembered values once, and a second SHALL be refused.
A form SHALL be raised as often as the round budget allows: a reader who skipped a box
left a gap cora cannot fill from anywhere else, and the alternative is the prose the form
exists to replace. A form raised with the rounds spent SHALL end the turn the way any
other tool asked for at the budget does.

#### Scenario: A second fork is refused

- **GIVEN** a turn that has already put a fork between two remembered values
- **WHEN** it asks a second time
- **THEN** the ask is refused, the reader is not stopped again, and the turn answers

#### Scenario: A form after a filled form still reaches the reader

- **GIVEN** a turn whose form came back with a required value skipped
- **WHEN** cora asks for what is still missing
- **THEN** a second card stands, and the reader is not asked for it in prose

#### Scenario: A round that asks both ways puts the one still open

- **GIVEN** a turn that has settled its fork already
- **WHEN** a round asks both for that fork again and for values
- **THEN** the reader is put the form, and never the same fork twice

### Requirement: A card that is not filled in cannot be sent

An action that runs on a card's values SHALL be unavailable while any required field is
empty, so the reader either fills the card in or leaves it by the way out. Whitespace
SHALL count as empty, and a value left empty SHALL NOT reach the turn as one the reader
wrote.

#### Scenario: The way out is the only way off an unfilled card

- **GIVEN** a card whose required field is empty
- **WHEN** the reader looks at what it offers
- **THEN** the action that submits is unavailable and says so, and the way out is not

#### Scenario: A box holding only spaces is not an answer

- **GIVEN** a card whose required field holds only spaces
- **WHEN** the reader looks at what it offers
- **THEN** the action that submits is still unavailable

#### Scenario: A skipped box is not reported as filled

- **GIVEN** a card the reader submitted with one box left empty
- **WHEN** the turn carries on
- **THEN** that field is absent from what the model is told and from the trace

### Requirement: An ask cora cannot read is refused, not put to the reader

An ask naming no field, or naming a field cora cannot read as one, SHALL be refused
where it was made. The reader SHALL NOT be shown a card they cannot answer, and the
turn SHALL carry on.

#### Scenario: An ask for nothing is refused

- **GIVEN** a turn that asks the reader for no fields at all
- **WHEN** the ask is read
- **THEN** it is refused, no card is put up, and the turn answers
