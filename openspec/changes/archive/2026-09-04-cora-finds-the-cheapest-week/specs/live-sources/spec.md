As a traveller,\
I want the cheapest flights and hotels for a window I have not fixed yet,\
so that I can tell whether the trip fits my budget before I settle the dates.

## ADDED Requirements

### Requirement: The travel scope prices a trip from a live search service

The travel scope SHALL offer a tool that searches flights and one that searches
accommodation, both against a live service. Each SHALL return at most three options,
cheapest first, and each option SHALL carry its price, its currency and its dates.

#### Scenario: The three cheapest flights for a route and a date

- **GIVEN** the travel scope, active, and the service configured
- **WHEN** the turn asks what flights to a destination cost
- **THEN** at most three options come back, cheapest first, each priced and dated

#### Scenario: The three cheapest places to stay

- **GIVEN** the same scope and a destination with a check-in and a check-out
- **WHEN** the turn asks what a week there costs
- **THEN** at most three options come back, cheapest first, each priced for the stay

#### Scenario: Priced in the currency the service answered in

- **GIVEN** an option the service priced
- **WHEN** it reaches the answer
- **THEN** its currency is stated, and no figure is converted into another one

#### Scenario: They are offered in their own field only

- **GIVEN** a turn running in another scope
- **WHEN** the tools available to it are read
- **THEN** neither search is among them

### Requirement: A window the traveller has not fixed is searched across departures

Where the traveller gives a range of months and a trip length rather than two dates, the
flight search SHALL try several departures inside that range and report the cheapest it
found. The answer SHALL name the dates each option belongs to.

#### Scenario: A month range and a length instead of two dates

- **GIVEN** a request for one week somewhere between two named months
- **WHEN** the search runs
- **THEN** several departures across that range are tried, and each option names its dates

#### Scenario: How closely the range is sampled can be asked for

- **GIVEN** the same request, with the traveller asking for every day to be tried
- **WHEN** the search runs
- **THEN** it samples the range more closely than it does unasked

#### Scenario: Two fixed dates are searched as given

- **GIVEN** a request naming a departure and a return
- **WHEN** the search runs
- **THEN** those dates are searched, and no other departure is tried

### Requirement: A budget and a restriction are held by the search

A price ceiling and a restriction the traveller states SHALL be applied by the search
itself. An option breaching one SHALL NOT be returned, and SHALL NOT be returned with a
caveat attached.

#### Scenario: An option above the ceiling never appears

- **GIVEN** a stated budget for the trip
- **WHEN** the search returns
- **THEN** no option above that ceiling is among the three

#### Scenario: A kind of accommodation ruled out stays out

- **GIVEN** a traveller who has ruled out a kind of place to stay
- **WHEN** the search returns
- **THEN** no place of that kind is among the three

#### Scenario: Nothing survives the restrictions

- **GIVEN** a budget and restrictions that leave the service with no option
- **WHEN** the search returns
- **THEN** the turn says so plainly, and invents nothing to fill the gap

### Requirement: A live source needing a credential is offered only where one is set

A tool whose service needs a credential SHALL be registered only where the deployment
configured one, read from that plugin's own slice of the environment. Where none is
set, the tool SHALL be absent rather than present and failing.

#### Scenario: No credential configured

- **GIVEN** a deployment loading the plugin with no key set for it
- **WHEN** the plugin's contributions are listed
- **THEN** neither search appears, and the scope's other tools are unaffected

#### Scenario: A credential configured

- **GIVEN** the same deployment with the key set
- **WHEN** the plugin's contributions are listed
- **THEN** both searches appear

#### Scenario: The key never reaches the model or the trace

- **GIVEN** a turn that called one of the searches
- **WHEN** the trace and the answer are read
- **THEN** neither carries the key
