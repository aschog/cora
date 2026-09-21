As someone learning words,\
I want a session to start German-first, in German, without spacing,\
so that sitting down to practise costs no setting-up.

## ADDED Requirements

### Requirement: A list is German first

The left column of a vocabulary list SHALL be the German one, and a drill SHALL put that
side unless the reader asks for the other. The field SHALL NOT ask which way round
before the first word.

#### Scenario: The first word of a session

- **GIVEN** a list whose left column is German
- **WHEN** the first word is put
- **THEN** it is the German side, and nothing was asked first

#### Scenario: The reader turns it round

- **WHEN** the reader asks to be asked from the other language
- **THEN** the other side is put from then on

### Requirement: The field speaks German

The vocab field SHALL speak German: what it says around a word, what it says about how
an answer went, and the hints it builds.

#### Scenario: A word is put

- **WHEN** a word is put to the reader
- **THEN** what is said around it is German

### Requirement: Spacing is off unless it is asked for

Spaced repetition SHALL be off unless the reader turns it on. While it is off, the
field SHALL write nothing to the schedule it keeps, so turning it on later begins from
a clean one rather than inheriting every pass.

#### Scenario: A session with spacing off

- **GIVEN** a reader who has not asked for spacing
- **WHEN** a word is answered
- **THEN** the schedule in the store is unchanged

#### Scenario: Spacing turned on

- **GIVEN** a reader who has asked for spacing
- **WHEN** a word is answered
- **THEN** the schedule moves as it does today

### Requirement: A session is one shuffled pass

With spacing off, a session SHALL be one pass over the chosen list in a shuffled order,
each word put once. A word answered right SHALL NOT come back in that pass, and a word
missed SHALL. Order SHALL NOT follow the list, so a word is learnt rather than its
place.

#### Scenario: Every word once

- **GIVEN** a list of three words and spacing off
- **WHEN** each is answered right in turn
- **THEN** three words were put, all three different

#### Scenario: A word missed comes back

- **GIVEN** a word answered wrongly
- **WHEN** the pass goes on
- **THEN** that word is put again before the pass ends

#### Scenario: Not the order of the list

- **GIVEN** a list long enough to tell
- **WHEN** two sessions are run over it
- **THEN** the order differs between them

### Requirement: A finished pass says so, and can be run again

When every word of the pass has been answered right, the field SHALL say the pass is
done rather than put a word. Asked to go again, it SHALL reshuffle the same list and
start a fresh pass.

#### Scenario: The pass ends

- **GIVEN** every word of the list answered right
- **WHEN** another word is asked for
- **THEN** the field says the pass is done

#### Scenario: Going again

- **GIVEN** a finished pass
- **WHEN** the reader asks to go again
- **THEN** words are put again, over the same list

### Requirement: What a session was set to lasts the conversation

The side being asked, whether spacing is on, and how far the pass has got SHALL be kept
for the conversation and no longer. A new conversation SHALL start German-first with
spacing off and a fresh pass.

#### Scenario: A new conversation

- **GIVEN** a conversation where the reader turned spacing on and the drill round
- **WHEN** a new conversation begins
- **THEN** it puts German first with spacing off
