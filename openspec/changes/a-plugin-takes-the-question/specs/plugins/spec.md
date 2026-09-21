As a plugin author,\
I want a handler that answers the question before the model is asked,\
so that a turn my plugin can settle itself costs no model call.

## MODIFIED Requirements

### Requirement: A plugin subscribes to a named point in the turn

The system SHALL let a plugin subscribe a handler to a named event: the question being
screened, the brief being settled, the question about to be worked, a tool call about to
run, and a tool result coming back. A handler SHALL be handed only frozen values and
SHALL answer by returning — a refusal, an amendment, an answer to the question, or
nothing. The system SHALL accept no handler that writes the turn's state, and SHALL
refuse a subscription to an event it does not have.

#### Scenario: A handler amends what the model is told

- **GIVEN** a plugin subscribing to the brief being settled
- **WHEN** a turn runs in its scope
- **THEN** what the handler returned is in the brief the model reads

#### Scenario: A handler takes the question

- **GIVEN** a plugin subscribing to the question about to be worked
- **WHEN** a turn runs in its scope and the handler answers with text
- **THEN** the reader reads that text, and the model is never asked

#### Scenario: A handler refuses a call before it runs

- **GIVEN** a plugin subscribing to the tool-call event and refusing one tool
- **WHEN** the model asks for that tool
- **THEN** the tool does not run, the model is told why, and the turn answers anyway

#### Scenario: A handler wraps what a tool returned

- **GIVEN** a plugin subscribing to a tool result coming back
- **WHEN** a tool it applies to returns
- **THEN** the model is told what the handler returned, not what the tool did

#### Scenario: What a handler is handed, it may read and not keep

- **GIVEN** a plugin whose handler rewrites the arguments of a call it is shown
- **WHEN** that call runs
- **THEN** it runs on the arguments the model asked for

#### Scenario: A handler cannot unlabel the user's own documents

- **GIVEN** a plugin whose handler replaces a passage with prose of its own
- **WHEN** the model is told what the tool returned
- **THEN** it is told behind the notice that says the material is the user's, not cora's

#### Scenario: A handler answers one call, and not another

- **GIVEN** a plugin whose handler answers with a result belonging to another call
- **WHEN** the round reads what came back
- **THEN** the call it made is the call that was answered

#### Scenario: A handler that returns nothing changes nothing

- **GIVEN** a plugin whose handler reads what it is handed and returns nothing
- **WHEN** a turn runs
- **THEN** the turn is unchanged, and the handler saw what it subscribed to

#### Scenario: An event cora does not have is refused by name

- **GIVEN** a plugin subscribing to an event cora does not name
- **WHEN** cora starts
- **THEN** it refuses, naming that module and the event it asked for

## ADDED Requirements

### Requirement: A plugin may take the question

The system SHALL offer the question to a plugin once its field is settled, before any
round is spent. The first handler to answer with text SHALL have answered the turn, and
no model SHALL be asked. What it wrote SHALL join the conversation as the round the turn
ended on, and SHALL be recorded as any answer is. It SHALL be offered to the handlers at
the answer like any other. A handler answering with nothing, with blank text, with
anything but text, or by raising SHALL leave the turn to the model. Inside the handler
the plugin SHALL read and keep what it kept for the conversation, as inside a tool call.
A handler registered under a field SHALL be offered questions in that field and no other.

#### Scenario: The question is taken

- **GIVEN** a plugin whose handler answers one question with text
- **WHEN** that question is asked in its field
- **THEN** the reader reads that text, and the model was never asked

#### Scenario: A question left alone

- **GIVEN** the same plugin
- **WHEN** a question its handler answers with nothing is asked
- **THEN** the model answers it as it always did

#### Scenario: A taken turn is in the conversation

- **GIVEN** a turn a plugin took
- **WHEN** the model is asked on the next turn
- **THEN** what the plugin wrote is in the transcript it reads, as the answer it was

#### Scenario: A taken turn is recorded

- **GIVEN** a turn a plugin took
- **WHEN** the conversation's turns are read back
- **THEN** that turn is there, holding what the plugin wrote

#### Scenario: The handlers at the answer still run

- **GIVEN** a plugin taking the question and another amending the answer
- **WHEN** the question is taken
- **THEN** the reader reads the amended text

#### Scenario: A handler that breaks leaves the turn to the model

- **GIVEN** a plugin whose handler raises when offered the question
- **WHEN** a question is asked in its field
- **THEN** the model answers, and the trace says the handler broke and not what it held

#### Scenario: What is kept while taking is kept

- **GIVEN** a plugin whose handler keeps a value for the conversation as it takes the question
- **WHEN** a tool of that plugin runs on a later turn of the conversation
- **THEN** the tool reads that value

#### Scenario: Another field's question is not offered

- **GIVEN** a plugin whose handler is registered under one field
- **WHEN** a question is asked in another field
- **THEN** the model answers it, and the handler was not offered it
