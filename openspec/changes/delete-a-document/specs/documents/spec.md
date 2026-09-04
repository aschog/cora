As a reader,\
I want to delete a document from the documents rail,\
so that one I uploaded by mistake stops being searched and cited.

## ADDED Requirements

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
