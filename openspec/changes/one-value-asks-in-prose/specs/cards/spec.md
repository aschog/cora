As a person cora is answering,\
I want a single missing value asked for in a sentence,\
so that one box does not cost me a turn.

## ADDED Requirements

### Requirement: A card asks for two values or more

A card that asks for exactly one value SHALL be refused before the reader is put it, and
the turn SHALL carry on. The model SHALL be told which value it was and to ask for it in
its answer. The rule SHALL hold over every card, whoever wrote it, and SHALL count the
fields the reader may write rather than the fields the card shows.

#### Scenario: A form of one value is asked for in prose

- **GIVEN** a turn whose answer needs one value nobody has written down
- **WHEN** cora asks the reader for it as a form
- **THEN** no card stands, the turn answers, and the answer asks for that value

#### Scenario: A plugin's card of one value is refused with its call

- **GIVEN** a tool whose card asks the reader for one value
- **WHEN** the model calls it without that value
- **THEN** no card stands, the tool does not run, and the round is told why

#### Scenario: The trace carries the card that was refused

- **GIVEN** a turn whose card was refused for asking one value
- **WHEN** the trace is read
- **THEN** it carries that ask as a call that failed, and says which value it wanted

#### Scenario: A card of no writable fields still stops the turn

- **GIVEN** a call awaiting approval, whose card shows the tool and no argument
- **WHEN** the turn reaches the gate
- **THEN** the reader is put the card, because nothing on it is being asked for

#### Scenario: A card of one field nobody writes in still stops the turn

- **GIVEN** a tool whose card shows one value it worked out, for confirming
- **WHEN** the model calls it
- **THEN** the reader is put the card, and the call runs on what they confirm

## MODIFIED Requirements

### Requirement: Cora asks for values it does not hold

Cora SHALL be able to stop a turn and ask the reader for named values it does not hold
and cannot look up. The ask SHALL name two values or more, SHALL reach the reader as one
card of them, and SHALL be cora's own — available to a deployment that has loaded no
plugin. An ask of a single value SHALL be refused, and cora SHALL ask for it in prose.

#### Scenario: Four values are asked as one card

- **GIVEN** a turn whose answer needs a route, two dates and a budget
- **WHEN** cora asks the reader for them
- **THEN** one card stands with a field for each, under a prompt saying what it is for

#### Scenario: One value is asked in the answer

- **GIVEN** a turn whose answer needs only a height nobody has written down
- **WHEN** cora asks for it
- **THEN** no card stands, and the answer asks for the height in a sentence

#### Scenario: A bare cora can ask

- **GIVEN** a cora with no plugin loaded
- **WHEN** the tools it offers are listed
- **THEN** one of them asks the reader for values, beside the one that settles a fact

#### Scenario: A field says what kind of value it is

- **GIVEN** cora asks for a day, a whole number, and one of three named choices
- **WHEN** the card is drawn
- **THEN** the reader is offered a date control, a number control, and those three

### Requirement: A form may be raised again where a fork may not

A turn SHALL put its fork between remembered values once, and a second SHALL be refused.
A form SHALL be raised as often as the round budget allows, where two values or more are
still missing: a reader who skipped those boxes left a gap cora cannot fill from anywhere
else. Where one box is all that is still missing, cora SHALL ask for it in prose. A form
raised with the rounds spent SHALL end the turn the way any other tool asked for at the
budget does.

#### Scenario: A second fork is refused

- **GIVEN** a turn that has already put a fork between two remembered values
- **WHEN** it asks a second time
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

- **GIVEN** a turn that has settled its fork already
- **WHEN** a round asks both for that fork again and for values
- **THEN** the reader is put the form, and never the same fork twice
