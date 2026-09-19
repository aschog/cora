As someone training,\
I want the exercise rows to show the exercises and nothing else,\
so that the list reads as a list.

## MODIFIED Requirements

### Requirement: The fitness field brings a trainer

The fitness plugin SHALL bring its field a page: a plan of exercises worked one at a
time, each with its sets, its weight and whatever clips it has, and a camera to film
against. An exercise's row SHALL carry its number and its name, and no count of sets or
weight. The plan SHALL be read from the sheet the page names, and the page SHALL hand
what it produces to cora and to nothing else. Every other address it reaches SHALL be one
written down, so a new one is a change somebody made rather than a change nobody saw.

#### Scenario: The field is opened

- **GIVEN** the fitness plugin loaded
- **WHEN** the reader asks what fields have a page
- **THEN** fitness is named with the path its trainer is served under

#### Scenario: The trainer is worked

- **GIVEN** the trainer drawn
- **WHEN** the reader logs a set of the current exercise
- **THEN** that set reads as done, and the exercise reads complete once all its sets do

#### Scenario: A row is the exercise

- **WHEN** the rows are read
- **THEN** each carries its number and its name, and no count of sets or weight

#### Scenario: Where it reaches

- **WHEN** the addresses in the page are read
- **THEN** the only one it posts to is cora's own, and every other host is one the
  plugin's own suite names
