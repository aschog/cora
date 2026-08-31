## MODIFIED Requirements

### Requirement: A turn runs under the scopes it was given

The system SHALL run a turn under the scope its conversation is pinned to, or the one its
caller named, or the one it routed the question to. A deployment SHALL name in the
environment the scopes a turn may run under, and a deployment naming one SHALL leave
routing nothing to choose. A turn SHALL keep the scope it settled on for as long as it
lasts.

#### Scenario: The deployment says what its cora is for

- **GIVEN** a deployment naming one scope beside the plugins it loaded
- **WHEN** anyone asks anything
- **THEN** that scope's instructions and tools are what the turn runs with, unrouted

#### Scenario: The caller of one turn says otherwise

- **GIVEN** the same deployment
- **WHEN** a turn is asked for under a scope of its own
- **THEN** it runs under that one instead

#### Scenario: The pin outranks the reading of the question

- **GIVEN** a conversation pinned to one of two available scopes
- **WHEN** a question belonging to the other is asked
- **THEN** the turn runs under the pinned scope, and the question is not routed

#### Scenario: A turn that stopped to ask resumes under the same scopes

- **GIVEN** a scoped turn that stopped to put a decision to the user
- **WHEN** it is resumed
- **THEN** the rest of it runs under the scopes it started under
