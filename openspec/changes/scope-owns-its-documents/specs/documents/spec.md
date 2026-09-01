As a person with material in more than one field,\
I want each scope's documents kept as readable files under a place named for that scope,\
so that I can see what cora has, and a second field is a directory rather than a
redesign.

## Purpose

Where the text behind a citation is kept: one readable file per source, under the field
that owns it, and what a search of one field is allowed to see.

## ADDED Requirements

### Requirement: A scope's documents are readable files of its own

The system SHALL keep each ingested document's cleaned text as one Markdown file, under
a directory named for the scope it was ingested into. A citation SHALL open onto that
file's text.

#### Scenario: A citation opens onto a file

- **GIVEN** a document ingested into a scope
- **WHEN** its cleaned text is kept
- **THEN** one Markdown file under that scope's directory holds it
- **AND** the citation opens onto that file

#### Scenario: Two uploads of one filename are two files

- **GIVEN** a filename uploaded twice, with different text each time
- **WHEN** both are ingested into one scope
- **THEN** each has a file of its own, and each citation opens onto the text it was cut
  from

#### Scenario: A document ingested into two scopes is two files

- **GIVEN** the same file uploaded into two scopes
- **WHEN** both are ingested
- **THEN** each scope's directory holds its own copy, and neither reads the other's

### Requirement: The text is kept once and read back from the file

The system SHALL keep the cleaned text in the file alone. The index SHALL keep
embeddings and the span each passage occupies, and a retrieved passage's text SHALL be
read from the file its span was measured in.

#### Scenario: Nothing duplicates the text

- **GIVEN** a document ingested into a scope
- **WHEN** what the index holds is read
- **THEN** it holds the passage's span and no copy of the passage's text

#### Scenario: A passage still comes back written

- **GIVEN** the same document
- **WHEN** a search returns one of its passages
- **THEN** the passage carries the text at its span, as the file holds it

#### Scenario: A passage whose file is gone is not returned

- **GIVEN** an indexed document whose file has been removed
- **WHEN** a search would return one of its passages
- **THEN** that passage is left out rather than returned empty

### Requirement: A search sees one scope

The system SHALL search only the documents of the scope the turn is running under. No
other scope's passage SHALL be retrieved or cited, and the documents listed SHALL be
that scope's.

#### Scenario: Only the active scope is searched

- **GIVEN** documents in two scopes
- **WHEN** cora searches in one of them
- **THEN** only that scope's sources can be retrieved or cited

#### Scenario: The listing shows the active scope

- **GIVEN** the same two scopes
- **WHEN** the documents held are listed for one of them
- **THEN** only that scope's documents are named

#### Scenario: An empty scope reads as empty

- **GIVEN** documents in one scope and none in another
- **WHEN** cora searches in the empty one
- **THEN** it finds nothing, and says nothing was uploaded rather than naming the other's

### Requirement: An upload names the field it lands in

The system SHALL take the scope an upload names and ingest it there. An upload naming no
scope SHALL land in the default scope, which SHALL be searchable as any other scope is.

#### Scenario: An upload with no scope has a home

- **GIVEN** a document uploaded with no scope chosen
- **WHEN** it is ingested
- **THEN** it lands in the default scope's directory
- **AND** a turn running in the default scope can retrieve it

#### Scenario: The named field is where it lands

- **GIVEN** a document uploaded naming one of the loaded scopes
- **WHEN** it is ingested
- **THEN** it lands in that scope's directory, and a turn in that scope retrieves it

#### Scenario: A field nobody loaded is refused

- **GIVEN** a document uploaded naming a scope no plugin registered under
- **WHEN** it is ingested
- **THEN** it is refused, and the refusal names the fields there are

### Requirement: The page says which field a document goes into

The system SHALL let the reader choose the field an upload lands in, from the fields the
deployment loaded and the default scope. A pinned conversation SHALL offer its own field
as the one chosen.

#### Scenario: The reader picks the field

- **GIVEN** two scopes loaded and a conversation pinned to neither
- **WHEN** the reader uploads a document
- **THEN** they choose which field it goes into, the default scope among the choices

#### Scenario: A pinned conversation uploads into its own field

- **GIVEN** a conversation pinned to a scope
- **WHEN** the reader uploads a document
- **THEN** it goes into that field

#### Scenario: One field leaves nothing to choose

- **GIVEN** a deployment that loaded no scopes
- **WHEN** the reader uploads a document
- **THEN** no field is asked for, and it lands in the default scope

### Requirement: The layout is written down

The system SHALL state in `README.md` where a scope's documents are kept, in a
paragraph.

#### Scenario: README states the layout

- **WHEN** `README.md` is read
- **THEN** a paragraph names the directory per scope and the file per source
