# cards Specification

## Purpose
What a turn that stopped puts in front of the reader, and how it is settled. A card is
data cora wrote, so what can be asked for grows without the page being rebuilt.

## Requirements

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

### Requirement: What the reader writes settles the ask

The values the reader writes SHALL reach the turn that asked, and the answer SHALL rest
on them. A reader who writes nothing SHALL settle the ask too: the turn SHALL carry on
without the values and SHALL say what it still needs. A card that asked for nothing —
one the reader is put to confirm — SHALL settle on the action alone, and the model SHALL
be told what happened rather than that values were withheld.

#### Scenario: The turn answers on what was written

- **GIVEN** a turn stopped asking for a departure city and a day
- **WHEN** the reader writes them and submits the card
- **THEN** the turn continues and its answer rests on that city

#### Scenario: Nothing written still settles it

- **GIVEN** a turn stopped asking for a departure city and a day
- **WHEN** the reader takes the way out without writing either
- **THEN** the turn answers without them and says plainly what it still needs

#### Scenario: A confirmed card is not reported as filled in

- **GIVEN** a turn stopped on a card of read-only fields, which the reader confirms
- **WHEN** the tool runs
- **THEN** the model is told what it returned, and not that the reader gave nothing

#### Scenario: A card left unconfirmed says that, and not that a value was withheld

- **GIVEN** that same card, which the reader leaves
- **WHEN** the turn carries on
- **THEN** the model is told it was not confirmed, and answers saying it did not run

#### Scenario: The trace carries the ask

- **GIVEN** a turn that stopped for values and was answered
- **WHEN** the trace is read
- **THEN** it says what was asked for and which fields came back filled

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

### Requirement: A card that is not filled in cannot be sent

An action that runs on a card's values SHALL be unavailable while any required field is
empty, so the reader either fills the card in or leaves it by the way out. Whitespace
SHALL count as empty. A box that came up empty and went back empty SHALL NOT reach the
turn as a value the reader wrote, and a box that came up holding something and went back
empty SHALL reach it as the erasure it is.

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

#### Scenario: A value the reader cleared is cleared for the tool too

- **GIVEN** a card put up holding an argument the model wrote
- **WHEN** the reader empties that box and submits the card
- **THEN** the tool runs without that value, rather than on the one they cleared

### Requirement: An ask cora cannot read is refused, not put to the reader

An ask naming no field, or naming a field cora cannot read as one, SHALL be refused
where it was made. The reader SHALL NOT be shown a card they cannot answer, and the
turn SHALL carry on.

#### Scenario: An ask for nothing is refused

- **GIVEN** a turn that asks the reader for no fields at all
- **WHEN** the ask is read
- **THEN** it is refused, no card is put up, and the turn answers
