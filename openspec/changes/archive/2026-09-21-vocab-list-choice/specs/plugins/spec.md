As someone learning words,\
I want to choose which list I am drilling when I sit down to practise,\
so that a session is the words I meant and not every word I own.

## ADDED Requirements

### Requirement: A drill runs over the list the reader chose

Where the vocab field holds more than one list, a drill SHALL NOT begin until the reader
has chosen one of them or all of them. Asked for a word with nothing chosen, the field
SHALL refuse and name the lists it holds, so the choice is put to the reader before a
word is.

#### Scenario: Nothing chosen yet

- **GIVEN** a field holding two lists and no choice made
- **WHEN** a word is asked for
- **THEN** the call is refused and the refusal names both lists

#### Scenario: One list chosen

- **GIVEN** a field holding two lists
- **WHEN** one of them is chosen and a word is asked for
- **THEN** the word comes from that list and never from the other

#### Scenario: All of them chosen

- **GIVEN** a field holding two lists
- **WHEN** all of them are chosen
- **THEN** words from both are put

#### Scenario: A list that is not there

- **WHEN** a list the field does not hold is chosen
- **THEN** the call is refused and the refusal names the lists it does hold

### Requirement: One list is drilled without asking

Where the field holds exactly one list, a drill SHALL run over it without anything being
chosen: there is nothing to choose between, and a card offering one option is a question
already answered.

#### Scenario: The only list

- **GIVEN** a field holding one list and no choice made
- **WHEN** a word is asked for
- **THEN** a word from that list is put

### Requirement: The choice is asked once and lasts the conversation

What was chosen SHALL be kept for the conversation and read on every later word, so the
reader is asked once rather than once per word. It SHALL NOT outlive the conversation: a
new one begins by choosing again.

#### Scenario: Asked once

- **GIVEN** a list chosen and a word put
- **WHEN** the next word is asked for with nothing chosen again
- **THEN** it comes from the same list, and nothing is refused

#### Scenario: A new conversation chooses again

- **GIVEN** a list chosen in one conversation
- **WHEN** a word is asked for in another
- **THEN** the call is refused until a list is chosen there too
