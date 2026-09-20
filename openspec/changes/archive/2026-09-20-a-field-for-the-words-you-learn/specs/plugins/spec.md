As someone learning a language,\
I want a field that holds my word lists and answers from them,\
so that a word I met once is answered from the list I met it on.

## ADDED Requirements

### Requirement: A vocabulary field is brought by a plugin

A plugin SHALL bring cora a `vocab` field carrying instructions and nothing else. The
field SHALL hold vocabulary lists as its documents, and SHALL be offered and worked in
exactly as a field with no page is.

#### Scenario: The field is offered

- **GIVEN** the vocab plugin loaded
- **WHEN** the reader asks what fields there are
- **THEN** vocab is among them

#### Scenario: What it registers

- **GIVEN** the vocab plugin loaded
- **WHEN** what it registered is read
- **THEN** it is instructions under the vocab field, and no tool and no page

### Requirement: A word is answered from the list it is on

A question about a word asked in the vocab field SHALL be answered from the lists that
field holds, citing the list the word was found on. A word on none of them SHALL be
said to be on none of them, and SHALL NOT be written into one.

#### Scenario: A word that is on a list

- **GIVEN** a Markdown list of words uploaded to the vocab field
- **WHEN** the reader asks what one of its words means
- **THEN** the answer comes from that list and cites it

#### Scenario: A word that is on no list

- **GIVEN** a field whose lists do not hold the word asked about
- **WHEN** the reader asks what it means
- **THEN** the answer says the word is on none of the lists
