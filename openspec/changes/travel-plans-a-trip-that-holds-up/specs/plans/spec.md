As a traveller,\
I want cora to work out a whole trip that actually fits what I asked for,\
so that I get a plan that holds together rather than a description of one.

## Purpose

What a planned trip is, what it promises, and what happens when it cannot be made to
hold. A plan is checked before it is offered, and what could not be solved is said
rather than smoothed over.

## ADDED Requirements

### Requirement: One instruction plans a whole trip

Given a destination, a rough window and what the traveller wants, cora SHALL come back
with a plan: the days, a priced fare, a priced stay and the total. It SHALL work out the
steps itself, without being told which to take.

#### Scenario: A trip is planned from one sentence

- **GIVEN** the travel field, a search service and a question naming a place, a month and a budget
- **WHEN** the traveller asks for three days there
- **THEN** the answer carries a dated day-by-day plan, a fare, a stay and what the trip costs

#### Scenario: The traveller is not asked for the steps

- **GIVEN** the same question
- **WHEN** it is answered
- **THEN** no turn asks the traveller which search to run or in what order

### Requirement: A plan is checked before it is offered

Every plan SHALL be checked against what was asked, and a plan that fails a check SHALL
NOT be offered as though it passed. The checks SHALL cover at least: the stay covering
every night, the return matching the check-out, the total within the budget, every date
carrying something to do, and the nights planned matching the nights asked for.

#### Scenario: A plan over budget is not offered as it stands

- **GIVEN** a budget the cheapest candidate exceeds
- **WHEN** the trip is planned
- **THEN** the answer does not present that candidate as meeting the budget

#### Scenario: A stay that ends before the flight home is caught

- **GIVEN** a stay whose check-out falls before the return date
- **WHEN** the plan is checked
- **THEN** that plan is rejected and another is searched for

#### Scenario: An empty day is caught

- **GIVEN** a plan whose second day has nothing in it
- **WHEN** the plan is checked
- **THEN** that plan is rejected and another is searched for

### Requirement: A plan is searched, not guessed

Cora SHALL price several candidate departures across the window, pair each with a stay
for its own dates, and choose on total cost. The chosen plan SHALL be the cheapest that
passes its checks.

#### Scenario: Several weeks are priced and the cheapest passing one wins

- **GIVEN** a window holding several candidate departures at different prices
- **WHEN** the trip is planned
- **THEN** the plan carries the cheapest departure whose plan passed its checks

#### Scenario: A cheaper candidate that fails a check is passed over

- **GIVEN** a cheapest candidate whose stay does not cover the nights
- **WHEN** the trip is planned
- **THEN** the next cheapest passing candidate is the one offered

### Requirement: A plan it cannot make work says what it could not solve

Where no candidate passes after the revisions allowed, cora SHALL offer the closest plan
it reached and name every check it failed. It SHALL NOT relax a constraint the traveller
gave, and SHALL NOT present a failing plan as one that holds.

#### Scenario: Nothing fits the budget

- **GIVEN** a budget no candidate in the window can meet
- **WHEN** the trip is planned
- **THEN** the answer gives the cheapest plan found and says plainly that it is over budget, by how much

#### Scenario: The budget is not quietly raised

- **GIVEN** the same question
- **WHEN** it is answered
- **THEN** nothing in the answer treats a higher budget as though the traveller had given it

### Requirement: A plan is kept, and a change revises it

The plan SHALL be kept for the conversation it was made in. A later turn asking for a
change SHALL revise the kept plan and check it again, rather than planning from the
start.

#### Scenario: Making it cheaper revises what was planned

- **GIVEN** a plan already made in this conversation
- **WHEN** the traveller asks for it cheaper
- **THEN** the answer carries the same trip re-searched under a lower ceiling, and is checked again

#### Scenario: A revision that cannot hold says so

- **GIVEN** a plan and a change no candidate can satisfy
- **WHEN** the traveller asks for it
- **THEN** the kept plan stands and the answer says which part of the change could not be met

### Requirement: The planning is on the trace

What the planner did SHALL be readable on the trace: the candidates it priced, the
checks that failed, and each revision it made.

#### Scenario: A reader follows the planning

- **GIVEN** a trip planned over two revisions
- **WHEN** the reader opens the trace
- **THEN** the candidates priced, the failed checks and both revisions stand under that call

### Requirement: What is saved is what was verified

Saving an itinerary SHALL write the plan cora checked, and the call put to the traveller
for approval SHALL describe that plan. The model SHALL NOT be able to alter the plan
between the check and the save.

#### Scenario: The approval describes the plan

- **GIVEN** a verified plan in this conversation
- **WHEN** cora offers to save it
- **THEN** the card describes that plan's dates, fare, stay and total

#### Scenario: The file holds the verified plan

- **GIVEN** the traveller approves the save
- **WHEN** the file is written
- **THEN** it holds the plan that passed its checks, and the answer says where it went

### Requirement: Without prices it still plans what it can

Where the deployment set no search key, cora SHALL still plan the days and check
everything that does not need a price, and SHALL say that the trip is unpriced.

#### Scenario: A plan with no service to price it

- **GIVEN** a deployment with no search key
- **WHEN** a trip is planned
- **THEN** the answer carries the days and says plainly that it could not price the trip
