As a page a field brought,\
I want to read a document back by the name the field lists it under,\
so that what was saved into the field is shown from the field, not from a second copy.

## ADDED Requirements

### Requirement: A document is read back by its name

The system SHALL answer a field's name for a document with every upload of that name,
each as the text the field kept, oldest first. An upload whose text is gone SHALL be left
out. A name nothing was uploaded under SHALL be answered as not there, in a sentence. A
field nobody loaded SHALL be refused as the listing refuses it. Another field's document
of that name SHALL NOT be answered.

#### Scenario: One name, two uploads

- **GIVEN** one filename uploaded twice into a field, with different text
- **WHEN** that name is read from that field
- **THEN** both texts come back, the first upload first

#### Scenario: A name nothing was uploaded under

- **WHEN** a name no upload carried is read from a field
- **THEN** the answer says it is not there

#### Scenario: A field nobody loaded

- **WHEN** a name is read from a field cora does not offer
- **THEN** it is refused, naming the fields there are

#### Scenario: Another field's document

- **GIVEN** one filename uploaded into two fields
- **WHEN** it is read from one of them
- **THEN** only that field's text comes back
