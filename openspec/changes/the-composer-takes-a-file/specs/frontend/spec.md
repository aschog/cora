As someone asking about a file,\
I want to add it where I am typing the question,\
so that the document and the question about it are one move apart.

## ADDED Requirements

### Requirement: A document is added from the composer

The page SHALL offer, beside the question being typed, a control that adds a file or a
photo to the field the conversation is in. It SHALL be the upload the rail already
makes: the same field, the same list, the same news and the same refusals. While an
upload is running the control SHALL say so and SHALL NOT start another.

#### Scenario: A file is added beside the question

- **GIVEN** a conversation in a field
- **WHEN** the reader adds a file from the composer
- **THEN** it is uploaded into that field and appears in that field's documents

#### Scenario: What it says while it runs

- **GIVEN** an upload started from the composer
- **WHEN** it has not finished
- **THEN** the control says an upload is running, and takes no second file

#### Scenario: A refusal is the same refusal

- **GIVEN** a file cora refuses
- **WHEN** it is added from the composer
- **THEN** the reader is told what the rail's control would have told them

### Requirement: The rail keeps the control it had

The rail's own control for adding a document SHALL remain where it is, over the list it
changes, so a reader working in the documents does not have to reach the conversation
to add one.

#### Scenario: Both controls add to the same field

- **GIVEN** a conversation fixed to a field
- **WHEN** a document is added from the rail and another from the composer
- **THEN** both are documents of that field
