As someone learning words,\
I want a right answer to get the next word from the drill itself,\
so that practising runs at my pace and not at the model's.

## ADDED Requirements

### Requirement: A right answer is the drill's to take

While a word is on the table, an answer that is its other side — case aside, and a
closing full stop aside — SHALL be taken by the drill: the word is recorded as produced,
the next word of the pass is put, and no model is asked. The reader SHALL read that next
word alone. An answer that is not the word, a hint asked for, a right answer to the last
word of a pass, and every answer in a spaced session SHALL reach the model as they do
today. A right answer given after the model was asked while the word stayed on the table
SHALL count as missed, because what the model gave was a hint. The field's instructions
SHALL say that a right answer never reaches the model, and that the word on the table is
the last one put, whoever put it.

#### Scenario: A right answer

- **GIVEN** `Hund` on the table, asking for the English
- **WHEN** the reader answers `dog`
- **THEN** they read the next word alone, the pass is one word shorter, and the model was not asked

#### Scenario: Case and a full stop do not count

- **GIVEN** `Hund` on the table
- **WHEN** the reader answers `Dog.`
- **THEN** it is taken as right

#### Scenario: Not the word

- **GIVEN** `Hund` on the table
- **WHEN** the reader answers `cat`
- **THEN** the model is asked, and the pass has not moved

#### Scenario: A hint asked for

- **GIVEN** a word on the table
- **WHEN** the reader answers `h`
- **THEN** the model is asked

#### Scenario: Right after a hint

- **GIVEN** the model was asked and `Hund` stayed on the table
- **WHEN** the reader then answers `dog`
- **THEN** they read the next word, and `Hund` comes round again in the pass

#### Scenario: The last word

- **GIVEN** the last word of the pass on the table
- **WHEN** the reader answers it right
- **THEN** the model is asked, so the pass is closed and going again is offered

#### Scenario: A spaced session

- **GIVEN** a session the reader asked to space
- **WHEN** they answer right
- **THEN** the model is asked

#### Scenario: The other way round

- **GIVEN** the drill putting the other side, and `dog` on the table
- **WHEN** the reader answers `Hund`
- **THEN** it is taken as right

#### Scenario: The model reads the taken words

- **GIVEN** three words taken in a row
- **WHEN** the model is next asked
- **THEN** the words put and the answers given are in what it reads

#### Scenario: The instructions say so

- **WHEN** the field's instructions are read
- **THEN** they say a right answer never reaches the model, and the word on the table is the last one put
