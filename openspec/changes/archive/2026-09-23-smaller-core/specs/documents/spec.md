## MODIFIED Requirements

### Requirement: An upload names the field it lands in

The system SHALL take the scope an upload names and land it there, as a file of that
field under the name it was uploaded as. An upload naming no scope SHALL land in the
default scope, which SHALL be searchable as any other scope is. The file SHALL be kept
whether or not a plugin indexes it, and what is indexed of it SHALL be that plugin's.

#### Scenario: An upload with no scope has a home

- **GIVEN** a document uploaded with no scope chosen
- **WHEN** it lands
- **THEN** it is a file of the default scope
- **AND** a plugin indexing it does so there

#### Scenario: The named field is where it lands

- **GIVEN** a document uploaded naming one of the loaded scopes
- **WHEN** it lands
- **THEN** it is a file of that scope, and a turn in that scope retrieves what was
  indexed of it

#### Scenario: A field nobody loaded is refused

- **GIVEN** a document uploaded naming a scope no plugin registered under
- **WHEN** it is uploaded
- **THEN** it is refused, and the refusal names the fields there are

#### Scenario: The file is among the field's files

- **GIVEN** a document uploaded into a field
- **WHEN** the field's files are listed
- **THEN** it is named among them

## ADDED Requirements

### Requirement: Deleting a document leaves the file it landed as

Deleting a document from the rail SHALL drop its passages and its kept text, and SHALL
leave the file it landed as among the field's files, where the field's own control
drops it.

#### Scenario: The passages go, the file stays

- **GIVEN** a document uploaded and then deleted from the rail
- **WHEN** the field's files are listed and the field is searched
- **THEN** the file is still named, and no passage of it comes back

### Requirement: An upload says it was taken, not how it was cut

The upload's answer SHALL name the document and the field it landed in, and SHALL NOT
count its passages, which are a plugin's business.

#### Scenario: The answer names the document and the field

- **WHEN** a file is uploaded
- **THEN** the answer names the document and the field, and the page says it was added
