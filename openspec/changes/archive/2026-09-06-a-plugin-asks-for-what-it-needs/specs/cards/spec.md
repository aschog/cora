As a plugin author,\
I want to ask the reader for the values my tool needs,\
so that I get them filled in without forking cora's page.

## Purpose

What a turn that stopped puts in front of the reader, and how it is settled. A card is
data cora wrote, so what can be asked for grows without the page being rebuilt.

## ADDED Requirements

### Requirement: A paused turn is put to the reader as one card

A turn that stops SHALL carry one card: a prompt, the fields the reader may fill, and
the actions they may take. The page SHALL draw any card from that shape alone, knowing
nothing of what stopped the turn.

#### Scenario: A card with fields is drawn

- **GIVEN** a turn stopped on a card of three fields and one action
- **WHEN** the page draws it
- **THEN** three controls and one button stand under the prompt

#### Scenario: A card with no fields is drawn

- **GIVEN** a turn stopped on a card of no fields and two actions
- **WHEN** the page draws it
- **THEN** two buttons stand under the prompt, and no control does

#### Scenario: A reload finds the card

- **GIVEN** a turn stopped on a card
- **WHEN** the conversation is reopened
- **THEN** the same card stands under the question that raised it

### Requirement: A field says what it is, and the page draws what it says

Each field SHALL carry the JSON Schema of the value asked for. The page SHALL draw the
control that schema describes, and a schema it cannot draw SHALL fall back to text
rather than to nothing.

#### Scenario: A dated field is drawn as a date

- **GIVEN** a field whose schema is a string of format `date`
- **WHEN** the page draws it
- **THEN** the reader is offered a date control

#### Scenario: A field of few choices is drawn as choices

- **GIVEN** a field whose schema enumerates three values
- **WHEN** the page draws it
- **THEN** the reader is offered those three and no free text

#### Scenario: A schema the page has no control for still asks

- **GIVEN** a field whose schema names a type the page does not draw
- **WHEN** the page draws it
- **THEN** the reader is offered a text control, and the card is usable

### Requirement: An action may wait for the card to be filled

An action SHALL be able to require that every required field holds a value. Such an
action SHALL be untakeable until they do, and SHALL say so where its label stands.

#### Scenario: An unfilled card cannot be submitted

- **GIVEN** a card with a required field left empty
- **WHEN** the reader looks at the action requiring it
- **THEN** it cannot be taken, and it says the card must be filled first

#### Scenario: A filled card can be submitted

- **GIVEN** the same card with every required field holding a value
- **WHEN** the reader looks at that action
- **THEN** it can be taken

#### Scenario: An action requiring nothing is always takeable

- **GIVEN** a card with a required field left empty and an action requiring nothing
- **WHEN** the reader takes that action
- **THEN** the turn goes on

### Requirement: Settling a card carries what the reader wrote

Resuming a paused turn SHALL carry the action taken and the values entered. The turn
SHALL go on with those values, and a turn settled by an action of no fields SHALL carry
the action alone.

#### Scenario: The values reach the turn

- **GIVEN** a card whose fields the reader filled
- **WHEN** they take the action that submits it
- **THEN** the turn continues with exactly those values

#### Scenario: An answered card reads as settled

- **GIVEN** a card the reader has settled
- **WHEN** they read back up the conversation it stood in
- **THEN** the card says which action was taken, where it stood

### Requirement: A card is data, and drawing it runs nothing

A card SHALL be data alone: prompt, fields and actions. The page SHALL treat every part
of it as text to draw, and SHALL execute nothing a card carries, whichever plugin wrote
it.

#### Scenario: A card carrying markup is drawn as text

- **GIVEN** a card whose prompt and labels carry markup
- **WHEN** the page draws it
- **THEN** the markup is shown as written, and none of it is run

### Requirement: A decision and a proposal are cards

What cora stops to ask, and what it stops to propose, SHALL both reach the page as
cards. A decision SHALL be a card of options and no fields; a proposal SHALL be a card
whose fields are the call's arguments, which the reader reads and cannot write.

#### Scenario: A decision is still answered by picking one

- **GIVEN** cora stopped to ask which of two values is current
- **WHEN** the reader picks one
- **THEN** the turn goes on with it, and the card says what they chose

#### Scenario: A proposal still shows the call and waits

- **GIVEN** cora stopped on a call that would change something outside it
- **WHEN** the page draws it
- **THEN** the tool and every argument stand there, and none of them is writable

#### Scenario: A declined proposal still changes nothing

- **GIVEN** a proposal the reader declines
- **WHEN** the turn goes on
- **THEN** nothing outside cora changed, and the answer says what was refused

### Requirement: A gathering tool is offered saying so, and with nothing required

A tool declaring `asks` SHALL be offered to the model saying it asks for what is missing,
and with no required arguments. The schema the plugin registered SHALL be unchanged, and
every call SHALL still be run against it.

#### Scenario: The model is told it may call unfilled

- **GIVEN** a tool that gathers, whose registered schema requires an argument
- **WHEN** the model is offered it
- **THEN** the schema it is offered requires none, and the registered one still requires it

#### Scenario: What the tool takes is unchanged

- **GIVEN** that tool, called without the argument it requires
- **WHEN** the call runs
- **THEN** it is refused for the argument it is missing

#### Scenario: A tool that gathers nothing is offered as registered

- **GIVEN** a tool declaring no card
- **WHEN** the model is offered it
- **THEN** its schema is exactly the one registered, required arguments and all

### Requirement: The travel scope asks for a trip before it searches

The travel search SHALL ask for the trip as a card when it has not been told one. The
card SHALL offer the fields the search takes, and SHALL run only once the reader submits
it.

#### Scenario: An underspecified trip raises a card

- **GIVEN** the travel scope, and a question naming no route and no dates
- **WHEN** the reader names a trip they want to take
- **THEN** a card asks for the trip, and no search has run

#### Scenario: The submitted trip is what is searched

- **GIVEN** that card, filled with a route and a window
- **WHEN** the reader submits it
- **THEN** the search runs on those values, and the answer prices them
