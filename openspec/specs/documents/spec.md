# documents Specification

## Purpose

Where the text behind a citation is kept: one readable file per source, under the field
that owns it, what a search of one field is allowed to see, and what deleting one of
those documents takes with it.

## Requirements

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

### Requirement: A turn says which field it was answered in

The system SHALL report, with a turn's answer, the fields it ran in, and SHALL keep them
with the turn it recorded. The page SHALL draw a conversation in the field its turns were
answered in, where they name one.

#### Scenario: An unpinned turn names the field it was routed to

- **GIVEN** two fields loaded and no pin
- **WHEN** a question belonging to one is answered
- **THEN** the turn reports that field

#### Scenario: A reopened conversation is drawn in its own field

- **GIVEN** a recorded conversation whose turns were answered in one field
- **WHEN** it is reopened
- **THEN** its documents and citations are drawn in that field

#### Scenario: A field a turn was answered in outlives the page

- **GIVEN** a recorded turn
- **WHEN** it is read back from the store
- **THEN** it reports the field it was answered in

### Requirement: The layout is written down

The system SHALL state in `README.md` where a scope's documents are kept, in a
paragraph.

#### Scenario: README states the layout

- **WHEN** `README.md` is read
- **THEN** a paragraph names the directory per scope and the file per source

### Requirement: A document can be deleted from the rail it was uploaded into

The system SHALL offer, for each document a field lists, a way to delete that one. A
deleted document SHALL be gone from that field's listing, and its passages SHALL be
returned by no search of it.

#### Scenario: A deleted document leaves the listing

- **GIVEN** a field holding two indexed documents
- **WHEN** one of them is deleted
- **THEN** the field lists the other one alone

#### Scenario: A deleted document answers nothing

- **GIVEN** a question the deleted document was the only answer to
- **WHEN** that question is asked after the delete
- **THEN** no passage of it comes back, and the turn is still answered

#### Scenario: Its text is gone from the field's directory

- **GIVEN** a deleted document
- **WHEN** the field's directory is read
- **THEN** the file that held its text is not there

### Requirement: Deleting a document takes every upload of that name

A field lists a document by the name it was uploaded under, and one name may be several
uploads. Deleting SHALL take every upload of that name in that field, so nothing of the
name is left to search or to open.

#### Scenario: One name uploaded twice goes at once

- **GIVEN** a field where one filename was uploaded twice, as two documents
- **WHEN** that name is deleted
- **THEN** neither upload is searchable, and neither file is left

#### Scenario: Another field's document of that name is untouched

- **GIVEN** the same file ingested into two fields
- **WHEN** it is deleted in one of them
- **THEN** the other field still lists it, and a search there still finds it

### Requirement: A document is uploadable again once it is deleted

The bytes name an upload, and an upload already indexed costs nothing to add again. A
deleted document SHALL be treated as new, so a reader who deletes one by mistake can put
it back.

#### Scenario: The same file uploaded after being deleted is indexed again

- **GIVEN** a document that was deleted
- **WHEN** the same file is uploaded into that field
- **THEN** it is indexed, and a search finds its passages

### Requirement: Deleting a document is asked about first

Deleting SHALL be confirmed before it happens, in the question the system already puts
over the page. The question SHALL name the document and say what is lost and what is
not. Nothing SHALL be deleted until it is confirmed.

#### Scenario: The control asks rather than deletes

- **GIVEN** a listed document
- **WHEN** the control on its row is used
- **THEN** the reader is asked, and the document is still listed

#### Scenario: Keeping the document deletes nothing

- **GIVEN** that question open
- **WHEN** the reader keeps the document instead
- **THEN** nothing is deleted, and the field still lists it

### Requirement: A citation into a document that is gone says so

An answer already given SHALL keep the citations it was written with. Opening a citation
whose document the system no longer holds SHALL say that in one sentence — the same
sentence whether the document was deleted or its text was never kept, because the store
holds no record of which.

#### Scenario: An old answer's citation cannot be opened

- **GIVEN** an answer citing a document that has since been deleted
- **WHEN** the reader opens that citation
- **THEN** they are told the document is no longer there, and the answer is unchanged

### Requirement: A document leaves the rail when the reader confirms it

The rail SHALL stop listing a document as soon as the reader confirms deleting it, before
the store has answered.

#### Scenario: The row goes before the store answers

- **GIVEN** a document the reader has confirmed deleting
- **WHEN** the store has not yet answered
- **THEN** the rail no longer lists it, and lists the others

### Requirement: A document the store would not delete comes back, with the reason

Where the store refuses the delete, the document SHALL be listed again and the page SHALL
say why.

#### Scenario: Refused, so it is listed again

- **GIVEN** a document the reader confirmed deleting
- **WHEN** the store refuses
- **THEN** it is listed again, and the page says why
