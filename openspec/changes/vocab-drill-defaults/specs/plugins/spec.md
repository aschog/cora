As someone learning words,\
I want a session to start German-first, in German, without spacing,\
so that sitting down to practise costs no setting-up.

## ADDED Requirements

### Requirement: A drill puts the German side, whichever column it is in

A drill SHALL put the German side of a pair unless the reader asks for the other, and
SHALL NOT ask the reader which way round before the first word. Which column holds the
German SHALL be said once per list and kept for good, because a page is photographed
whichever way round it was printed and nothing in the file says. A list nobody has said
it for SHALL be refused rather than guessed at, and the refusal SHALL carry enough of
its pairs to be answered from.

#### Scenario: The first word of a session

- **GIVEN** a list whose German column has been said
- **WHEN** the first word is put
- **THEN** it is the German side, and nothing was asked of the reader first

#### Scenario: A list read the other way round

- **GIVEN** a list whose right column is the German one
- **WHEN** a word is put
- **THEN** it is the right column, and the left is withheld

#### Scenario: A list nobody has sided

- **GIVEN** a list whose German column has not been said
- **WHEN** a word is asked for
- **THEN** the call is refused and the refusal shows some of that list's pairs

#### Scenario: Said once

- **GIVEN** a list whose German column was said in an earlier conversation
- **WHEN** a word is asked for in a new one
- **THEN** a word is put without anything being asked again

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

### Requirement: Only a word from the list is put

A word the reader is shown in a drill SHALL be one the drill put. Where the answer is a
single word and not the one on the table, the field SHALL replace it with the word it
puts next, and the word that was on the table SHALL come round again. Prose SHALL be
left as it is.

#### Scenario: A word from nowhere

- **GIVEN** `Apfel` on the table and `Apfelbaum` written as the answer
- **WHEN** the answer reaches the reader
- **THEN** it is a word from the list, and `Apfel` is still to be answered

#### Scenario: The word on the table

- **GIVEN** `Apfel` on the table and `Apfel` written as the answer
- **WHEN** the answer reaches the reader
- **THEN** it is `Apfel`, unchanged

#### Scenario: A sentence

- **GIVEN** a word on the table and a sentence written as the answer
- **WHEN** the answer reaches the reader
- **THEN** the sentence is unchanged

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
spacing off and a fresh pass. Which column is German is not one of these: it belongs to
the list, and is kept for good.

#### Scenario: A new conversation

- **GIVEN** a conversation where the reader turned spacing on and the drill round
- **WHEN** a new conversation begins
- **THEN** it puts German first with spacing off
