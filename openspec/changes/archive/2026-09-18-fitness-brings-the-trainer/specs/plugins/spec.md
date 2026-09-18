As someone training,\
I want the fitness field to open on a trainer I work the session in,\
so that what I actually lifted is logged where cora can answer about it.

## ADDED Requirements

### Requirement: The fitness field brings a trainer

The fitness plugin SHALL bring its field a page: a plan of exercises worked one at a
time, each with its sets, its weight and whatever clips it has, and a camera to film
against. The page SHALL carry its own plan rather than fetching one, and SHALL hand what
it produces to cora and to nothing else. Every other address it reaches SHALL be one
written down, so a new one is a change somebody made rather than a change nobody saw.

#### Scenario: The field is opened

- **GIVEN** the fitness plugin loaded
- **WHEN** the reader asks what fields have a page
- **THEN** fitness is named with the path its trainer is served under

#### Scenario: The trainer is worked

- **GIVEN** the trainer drawn
- **WHEN** the reader logs a set of the current exercise
- **THEN** that set reads as done, and the count on that exercise says so

#### Scenario: Where it reaches

- **WHEN** the addresses in the page are read
- **THEN** the only one it posts to is cora's own, and every other host is one the
  plugin's own suite names

### Requirement: A finished workout is a document of the fitness field

Finishing a workout SHALL upload it into the fitness field as a Markdown document named
for the day. The text SHALL be a heading per exercise carrying its load, followed by the
sets it took. An exercise nothing was logged for SHALL NOT appear.

#### Scenario: A workout is finished

- **GIVEN** a workout with sets logged against one exercise
- **WHEN** the reader finishes it
- **THEN** a document named for today is in the fitness field, holding that exercise and
  its sets

#### Scenario: An exercise that was not worked

- **GIVEN** a workout where one planned exercise logged nothing
- **WHEN** it is finished
- **THEN** the document does not name that exercise

#### Scenario: Nothing logged at all

- **WHEN** the reader finishes a workout with no set logged
- **THEN** nothing is uploaded

### Requirement: What the trainer logged is what cora answers from

A workout uploaded by the trainer SHALL be searched and cited as any other document of
that field is, so the reader can ask about what they lifted and be shown the day it came
from.

#### Scenario: Asking about what was lifted

- **GIVEN** a workout finished into the fitness field
- **WHEN** the reader asks about that exercise with the conversation in that field
- **THEN** the answer rests on that document and cites it

### Requirement: A workout that could not be saved is not lost

Where the upload fails, the page SHALL say so and SHALL keep the workout's text where the
reader can still take it. The workout SHALL be added to the page's own history either
way.

#### Scenario: The upload fails

- **GIVEN** a finished workout that cora refuses or cannot be asked
- **WHEN** the page reports it
- **THEN** it says the workout was not saved, and the text is still reachable

#### Scenario: The history holds it regardless

- **WHEN** a workout is finished, whether or not the upload succeeded
- **THEN** it is in the page's own history and a fresh workout starts
