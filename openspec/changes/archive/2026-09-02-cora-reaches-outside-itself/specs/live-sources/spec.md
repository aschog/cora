As a person asking about something my documents cannot know,\
I want cora to call a live service and answer from what it gets back,\
so that the answer is current instead of a polite refusal.

## Purpose

How cora answers from outside itself: a scope's tool onto a live service, how what it
returns is labelled, and what a failure out there costs the turn.

## ADDED Requirements

### Requirement: A scope's tool may reach a live service

A tool a plugin registers SHALL be free to call a service outside cora, and the turn
SHALL answer from what it returned. The trace SHALL name the call and what came back.

#### Scenario: A question that needs the outside world

- **GIVEN** a scope with a tool onto a live external service
- **WHEN** the turn asks something that needs current information
- **THEN** the service is called, and the answer rests on what it returned

#### Scenario: The trace names the call and its result

- **GIVEN** a turn that called such a tool
- **WHEN** the trace is read
- **THEN** it shows the call as made, and what came back from it

### Requirement: The travel scope reaches a live forecast

The travel scope SHALL offer a tool that fetches a forecast for a place and a span of
dates. It SHALL need no credential, so a deployment that names the plugin can call it.

#### Scenario: A forecast is fetched for a named place

- **GIVEN** the travel scope, active
- **WHEN** the turn asks what the weather will be somewhere
- **THEN** the tool resolves the place, fetches its forecast, and reports it

#### Scenario: A place the service does not know

- **GIVEN** a place name the service resolves to nothing
- **WHEN** the tool runs
- **THEN** it says so in one line, and no forecast is invented

#### Scenario: It is offered in its own field only

- **GIVEN** a turn running in another field
- **WHEN** the tools are offered to the model
- **THEN** the forecast tool is not among them

### Requirement: A tool declares that what it returns is not cora's own words

A plugin registering a tool SHALL be able to declare that its result is material cora
did not write. The declaration SHALL belong to the tool, holding for every call of it.

#### Scenario: A tool is registered as returning outside material

- **GIVEN** a plugin registering a tool with that declaration
- **WHEN** the tool is offered to a turn
- **THEN** it carries the declaration wherever a call of it is run

#### Scenario: Every call of it is labelled

- **GIVEN** a round asking for that tool twice
- **WHEN** both calls return
- **THEN** each result is labelled, the declaration being the tool's and not the call's

#### Scenario: A tool declaring nothing is unchanged

- **GIVEN** a tool registered without the declaration
- **WHEN** its result reaches the model
- **THEN** it arrives as it did before, unlabelled

### Requirement: What a service returns is untrusted data

Text a declaring tool returned SHALL reach the model behind the untrusted-data label,
exactly as a passage of the user's own documents does. No plugin SHALL take it off.

#### Scenario: The label is on what was fetched

- **GIVEN** a tool that fetched text from a service
- **WHEN** the result reaches the model
- **THEN** it is labelled untrusted data, with instructions in it never to be followed

#### Scenario: The label names where the material came from

- **GIVEN** the label as the model reads it
- **WHEN** it says what the material is
- **THEN** it names a service a tool called, as it already names the user's documents

#### Scenario: Instructions in the fetched text are not followed

- **GIVEN** a service whose response tells the model to ignore its brief
- **WHEN** the turn runs
- **THEN** the text arrives as data, under the same label a document's would

#### Scenario: A handler cannot take the label off

- **GIVEN** a plugin subscribed to the returning event
- **WHEN** it amends a labelled result
- **THEN** what reaches the model is still labelled

### Requirement: A service that fails costs the turn one call

A service that errors or times out SHALL cost the turn that call and nothing else. One
friendly line SHALL say so, and nothing SHALL be presented as an answer.

#### Scenario: The service is down

- **GIVEN** a service that fails or times out
- **WHEN** the turn runs
- **THEN** one friendly message says so, and the conversation is intact

#### Scenario: Nothing is invented in its place

- **GIVEN** the failed call
- **WHEN** the answer is written
- **THEN** it presents no forecast, and claims no source it did not get

#### Scenario: The failure is on the trace as the call's

- **GIVEN** the failed call
- **WHEN** the trace is read
- **THEN** that call is shown as failed, and the turn's other steps stand

### Requirement: An answer resting on a fetched result is cora's own prose

A fetched result SHALL be handed no citation number, and the answer SHALL read as
cora's own words. The trace SHALL be the whole record of where the answer came from.

#### Scenario: No number is handed out for what was fetched

- **GIVEN** a turn whose answer rests on what a service returned
- **WHEN** the turn's citations are read
- **THEN** none of them names the service, and a citation stays a passage of a document

#### Scenario: A document cited in the same turn still is

- **GIVEN** a turn that both searched the documents and fetched a result
- **WHEN** the answer cites a passage
- **THEN** that citation opens onto its file, unaffected by the fetch beside it

#### Scenario: The trace carries what the answer does not

- **GIVEN** a reader asking where a current fact came from
- **WHEN** they open the trace
- **THEN** the call and what it returned are there to read

### Requirement: A plugin reaches only for the technology its own manifest buys

A plugin SHALL be allowed the technology its own distribution declares, and no other.
The allowance SHALL be keyed per plugin, so one plugin's dependency is not every
plugin's.

#### Scenario: A plugin's allowance is what its manifest declares

- **GIVEN** a plugin allowed a technology by name
- **WHEN** its own manifest is read
- **THEN** the distribution contributing that name is declared there

#### Scenario: A plugin inherits nothing from its neighbour

- **GIVEN** a plugin with no allowance of its own
- **WHEN** it imports a technology another plugin was allowed
- **THEN** the guard fails, naming the file and what it reached for
