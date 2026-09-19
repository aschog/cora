As a plugin author,\
I want the host to hand my tool every document its field holds,\
so that a tool can list what was logged rather than search for it.

## ADDED Requirements

### Requirement: A plugin reads what its field holds

The host SHALL hand a plugin every document of the field the turn runs in. Each SHALL
come as its name and its text, the names in the order first uploaded and the uploads
of one name together, oldest first. Two uploads of one name SHALL be two documents. A document whose text is gone SHALL be left out. Another field's documents
SHALL NOT be among them.

#### Scenario: A field is read whole

- **GIVEN** two documents uploaded into a field, and a plugin's tool that lists what it
  holds
- **WHEN** the tool runs in a turn of that field
- **THEN** it is handed both, by name and by text, the first upload first

#### Scenario: One name, two uploads

- **GIVEN** one filename uploaded twice with different text
- **WHEN** the field is read
- **THEN** both texts come back, each under that name

#### Scenario: Another field is not read

- **GIVEN** a document in another field
- **WHEN** this field is read
- **THEN** it is not among them

#### Scenario: A file that is gone

- **GIVEN** a document whose text was deleted under cora
- **WHEN** the field is read
- **THEN** it is left out, and the rest come back

## MODIFIED Requirements

### Requirement: A plugin is handed cora's own parts

The host SHALL give a plugin what cora has: document search, its field's documents, what
cora remembers, and the model. It SHALL also give the plugin a log and settings of its
own, both named for the plugin rather than for cora.

#### Scenario: A plugin uses cora's own parts

- **GIVEN** a plugin that wants to search, to read its field, to remember, or to call the
  model
- **WHEN** it is loaded
- **THEN** the host it was handed offers each of those

#### Scenario: What a plugin logs and reads is named for it

- **GIVEN** a loaded plugin that writes a log line and reads a setting
- **WHEN** the line is written and the setting is read
- **THEN** both are named for that plugin

### Requirement: What a plugin read for cora is labelled untrusted

The system SHALL label as untrusted whatever reaches a model out of the user's documents.
This SHALL hold for the passages a plugin's own loop read, for what that loop answered
after reading them, and for a plugin that searched the documents itself. It SHALL hold
for a plugin that read its field whole.

#### Scenario: A delegated loop reads its passages behind the label

- **GIVEN** a loop that searched the user's documents
- **WHEN** it is shown what the search found
- **THEN** the passages arrive labelled untrusted, as a turn's own search labels them

#### Scenario: What a loop answered reaches the turn labelled

- **GIVEN** a tool whose loop read the documents and answered in its own words
- **WHEN** the turn's model is told what that tool returned
- **THEN** the answer arrives labelled untrusted, though it carries no passage

#### Scenario: A plugin that searches for itself says so

- **GIVEN** a plugin whose tool searches the documents without delegating
- **WHEN** the turn's model is told what that tool returned
- **THEN** the answer arrives labelled untrusted

#### Scenario: A plugin that reads its field says so

- **GIVEN** a plugin whose tool reads every document of its field
- **WHEN** the turn's model is told what that tool returned
- **THEN** the answer arrives labelled untrusted
