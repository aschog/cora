As a reader,\
I want something beside me to leave a word with the cora I am running,\
so that a field's page can follow what happens away from the screen.

## ADDED Requirements

### Requirement: A field keeps one notice

The system SHALL hold, for each field it offers, the last notice written to that
field, and SHALL answer it to whoever asks. A notice SHALL be a JSON object, and a
second notice SHALL replace the first whole rather than be merged into it. A field
SHALL keep a notice of its own, no field reading another's.

#### Scenario: A notice is written and read back

- **GIVEN** a field cora offers
- **WHEN** a notice is written to it and then asked for
- **THEN** what was written is answered

#### Scenario: A second notice

- **GIVEN** a field holding a notice naming two things
- **WHEN** a notice naming one of them is written
- **THEN** what is answered is the second notice alone

#### Scenario: One field's notice is not another's

- **GIVEN** two fields cora offers, each written a notice of its own
- **WHEN** each is asked for
- **THEN** each answers what was written to it

### Requirement: A notice says when cora heard it

The system SHALL record, on every notice it takes, the time it arrived by cora's own
clock, and SHALL answer that time with the notice. A time the writer states SHALL NOT
replace it, so no writer's clock has to agree with cora's.

#### Scenario: The arrival is answered with the notice

- **WHEN** a notice is written and then asked for
- **THEN** the answer carries the time cora took it

#### Scenario: A writer stating its own time

- **GIVEN** a notice carrying a time of the writer's own
- **WHEN** it is asked for
- **THEN** the time cora took it is the one the answer is stamped with

### Requirement: A field written to by nobody has no notice

The system SHALL answer that a field has no notice where none has been written, and
SHALL NOT treat that as a failure. A notice SHALL last as long as the process holding
it, and SHALL be gone when cora is started again.

#### Scenario: Nothing written yet

- **GIVEN** a field cora offers and nobody has written to
- **WHEN** its notice is asked for
- **THEN** the answer says there is none

#### Scenario: Cora is restarted

- **GIVEN** a field whose notice was written before cora was restarted
- **WHEN** its notice is asked for
- **THEN** the answer says there is none

### Requirement: A notice belongs to a field cora offers

The system SHALL refuse to hold or answer a notice for a name that is not a field of
the running composition, and SHALL say which fields there are. A field that arrives
with a plugin SHALL take a notice from that moment, and one whose plugin is gone
SHALL refuse both, the plugins folder being live.

#### Scenario: A name that is no field

- **WHEN** a notice is written to a name cora offers no field under
- **THEN** it is refused, and the refusal names the fields there are

#### Scenario: Asking for one

- **WHEN** the notice of a name that is no field is asked for
- **THEN** it is refused, and cora answers everything else as usual

#### Scenario: A field arrives with its plugin

- **GIVEN** a running cora, and a plugin bringing a field dropped into the folder
- **WHEN** a notice is written to that field
- **THEN** it is taken, with nothing restarted

### Requirement: A notice is small

The system SHALL refuse a notice larger than a few kilobytes, SHALL leave the held
notice unchanged when it does, and SHALL refuse a body that is not a JSON object.

#### Scenario: Too large

- **GIVEN** a field already holding a notice
- **WHEN** a notice past the ceiling is written
- **THEN** it is refused, and the held notice still answers

#### Scenario: Not an object

- **WHEN** a body that is not a JSON object is written
- **THEN** it is refused, and the held notice is unchanged
