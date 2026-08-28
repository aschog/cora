# frontend Specification

## Purpose

What cora is used through: one screen, served with the API from one process, and one
documented command that starts it.

## Requirements

### Requirement: cora is used through one screen

The system SHALL serve its page and its API from one process, and SHALL hold no second
frontend — not beside it as a choice, and not in the tree as code nobody runs.

#### Scenario: The page is served beside the API

- **WHEN** the shell is asked for the page and for the API
- **THEN** one process answers both

#### Scenario: The repository holds one frontend

- **WHEN** the frontends the workspace ships are listed
- **THEN** there is one, and it is the React shell

#### Scenario: No code reaches for the frontend that was removed

- **WHEN** the shipped code, the tests and the tooling are read
- **THEN** nothing imports Streamlit, and the check names any file that does
