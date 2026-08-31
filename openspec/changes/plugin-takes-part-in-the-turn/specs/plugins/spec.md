As someone writing a plugin,\
I want to act at a named point in the turn rather than only before it starts,\
so that I can amend what the model is told, refuse a call before it runs, or wrap what
comes back — without asking for a new field.

## ADDED Requirements

### Requirement: A plugin subscribes to a named point in the turn

The system SHALL let a plugin subscribe a handler to a named event: the question being
screened, the brief being settled, a tool call about to run, and a tool result coming
back. A handler SHALL be handed only frozen values and SHALL answer by returning — a
refusal, an amendment, or nothing. The system SHALL accept no handler that writes the
turn's state, and SHALL refuse a subscription to an event it does not have.

#### Scenario: A handler amends what the model is told

- **GIVEN** a plugin subscribing to the brief being settled
- **WHEN** a turn runs in its scope
- **THEN** what the handler returned is in the brief the model reads

#### Scenario: A handler refuses a call before it runs

- **GIVEN** a plugin subscribing to the tool-call event and refusing one tool
- **WHEN** the model asks for that tool
- **THEN** the tool does not run, the model is told why, and the turn answers anyway

#### Scenario: A handler wraps what a tool returned

- **GIVEN** a plugin subscribing to a tool result coming back
- **WHEN** a tool it applies to returns
- **THEN** the model is told what the handler returned, not what the tool did

#### Scenario: A handler that returns nothing changes nothing

- **GIVEN** a plugin whose handler reads what it is handed and returns nothing
- **WHEN** a turn runs
- **THEN** the turn is unchanged, and the handler saw what it subscribed to

#### Scenario: An event cora does not have is refused by name

- **GIVEN** a plugin subscribing to an event cora does not name
- **WHEN** cora starts
- **THEN** it refuses, naming that module and the event it asked for

### Requirement: Cora's own screen is a subscriber

The system SHALL run its own screening of what the user types as handlers on the same
event a plugin subscribes to, registered the same way and system-wide. It SHALL reach
them no other way.

#### Scenario: Cora's rules run as handlers

- **GIVEN** cora's own input rules and a plugin's, both loaded
- **WHEN** a turn runs
- **THEN** all of them ran as handlers on the screening event
- **AND** nothing in cora reached its own rules by another path

#### Scenario: Cora's own handlers run first

- **GIVEN** cora's own screening and a plugin's, both refusing the same question
- **WHEN** the turn runs
- **THEN** the refusal the user reads is cora's

### Requirement: Handlers chain in load order, and the trace names each plugin

The system SHALL run the handlers on one event in a stated order — its own first, then
the plugins as they were loaded — and each amendment SHALL be handed what the one before
it returned. The trace SHALL name the plugin behind every amendment and every refusal.

#### Scenario: Two handlers amend the same event

- **GIVEN** two plugins subscribing to the brief being settled
- **WHEN** a turn runs where both apply
- **THEN** the second was handed what the first returned, and the brief holds both

#### Scenario: The trace attributes an amendment to its plugin

- **WHEN** the trace of that turn is read
- **THEN** each amendment is named as that plugin's, in the order they ran

### Requirement: A handler fails closed when it refuses and open when it amends

The system SHALL treat a handler that raises on a refusing event as a refusal, so a
question or a call is never let through by a broken rule. A handler that raises on any
other event SHALL be dropped and the turn SHALL carry on without it. The trace SHALL
name the plugin in both cases.

#### Scenario: A rule that raises refuses the turn

- **GIVEN** a plugin whose screening handler raises
- **WHEN** a turn runs
- **THEN** the question is refused, and the trace names that plugin

#### Scenario: An amender that raises is dropped

- **GIVEN** a plugin whose brief handler raises
- **WHEN** a turn runs
- **THEN** the turn completes without that amendment, and the trace names that plugin

#### Scenario: An observer that raises is dropped

- **GIVEN** a plugin whose handler only watches, and raises
- **WHEN** a turn runs
- **THEN** the turn completes unchanged, and the trace names that plugin

#### Scenario: What a handler was holding stays out of what the user reads

- **GIVEN** a plugin whose handler raises carrying a value of its own
- **WHEN** the refusal or the trace is read
- **THEN** neither quotes what the handler was holding

### Requirement: A registration has a scope, and a system-wide one cannot be removed

Every registration SHALL carry a scope, and one carrying none SHALL be system-wide. The
system SHALL apply a registration when it is system-wide or when its scope is among the
turn's active ones, and SHALL offer no way for a scope to switch a system-wide one off.

#### Scenario: A scoped handler applies where it belongs

- **GIVEN** a handler registered under a named scope
- **WHEN** a turn runs in a different scope
- **THEN** it does not run

#### Scenario: A system-wide screen cannot be scoped away

- **GIVEN** a system-wide plugin loaded beside two scopes
- **WHEN** an injection attempt arrives in either scope, or with no scope active
- **THEN** it is refused before the model is called

#### Scenario: One plugin registers under two lifetimes

- **GIVEN** the fitness plugin, whose instructions and tools are its scope's
- **WHEN** its medical filter is registered
- **THEN** the filter is system-wide, and the instructions and tools are not

#### Scenario: The medical filter applies outside the scope it came from

- **GIVEN** the fitness plugin loaded
- **WHEN** a medical question is asked in another scope, or with no scope active
- **THEN** it is refused

## MODIFIED Requirements

### Requirement: A plugin registers what it has

The system SHALL load a plugin by calling `extend` on its module, and SHALL offer
whatever that call registered: its tools callable, its instructions in the brief, its
handlers taking part in the turn. The system SHALL accept no other way of contributing,
and SHALL offer no separate way to screen what the user types.

#### Scenario: A plugin registers rather than declares

- **GIVEN** a module defining `extend(cora)` and no record of contributions
- **WHEN** it is loaded
- **THEN** its tools are callable, its instructions are in the brief, and its handlers run

#### Scenario: The plugins cora ships carry no record

- **GIVEN** the security and fitness plugins as they are shipped
- **WHEN** their modules are read
- **THEN** each registers through `extend`, and neither leaves a record behind

#### Scenario: Screening is a subscription like any other

- **GIVEN** a plugin that wants to refuse what the user typed
- **WHEN** it registers
- **THEN** it subscribes to the screening event, there being no other way to ask
