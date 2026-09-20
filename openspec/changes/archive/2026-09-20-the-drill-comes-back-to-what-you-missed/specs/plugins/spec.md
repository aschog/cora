As someone learning words,\
I want the drill to come back to what I got wrong, on its own schedule,\
so that my time goes on the words I do not know yet.

## ADDED Requirements

### Requirement: The vocab field drills from a schedule it keeps

The vocab field SHALL keep a schedule of the words it has drilled, in its own store, and
SHALL hand back the word that is due when asked for one. A word never drilled SHALL
count as due. Where nothing is due and nothing is new, it SHALL say the session is done
rather than hand back a word.

#### Scenario: A word is asked for

- **GIVEN** a list in the vocab field and nothing drilled yet
- **WHEN** the reader asks to practise
- **THEN** a word from that list is put to them

#### Scenario: Nothing is due

- **GIVEN** every word on the list answered and scheduled beyond today
- **WHEN** the reader asks for another word
- **THEN** the field says the session is done rather than repeating a word

### Requirement: Only the side being asked is handed over

A word put to the reader SHALL carry the side they are being asked from and not the side
they are to produce, whichever way round the drill is running.

#### Scenario: What comes with the word

- **GIVEN** a drill running from German
- **WHEN** a word is put to the reader
- **THEN** the German is handed over and the word being learnt is not

### Requirement: What was missed comes back

Saying how a word went SHALL move that word's schedule and nothing else. A word missed
SHALL be due again in the same session. A word answered right SHALL be due a day later,
then six days, then at intervals that grow by how easy it has proved — never shorter
than the last one for a word answered right.

#### Scenario: A word missed

- **GIVEN** a word just put to the reader
- **WHEN** they miss it
- **THEN** it is among the words due in this session

#### Scenario: A word answered right

- **GIVEN** a word answered right for the first time
- **WHEN** the schedule is read
- **THEN** that word is due a day later, not today

#### Scenario: A word answered right twice

- **GIVEN** a word answered right on two days running
- **WHEN** the schedule is read
- **THEN** it is due six days later

#### Scenario: One word's answer moves one word

- **GIVEN** two words drilled
- **WHEN** one of them is answered
- **THEN** the other's schedule is what it was

### Requirement: The schedule outlives the conversation

The schedule SHALL be kept in the plugin's own store, so a session started tomorrow
picks up where today's left off, and SHALL NOT be a document of the field, in the brief,
or among what cora knows about the user.

#### Scenario: Tomorrow's session

- **GIVEN** words answered in one conversation
- **WHEN** the reader practises in another conversation
- **THEN** what they got wrong is what comes back

#### Scenario: The schedule is not a document

- **GIVEN** words answered in the vocab field
- **WHEN** the field's documents are listed
- **THEN** only the reader's own lists are there
