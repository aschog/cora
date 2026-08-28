As someone who runs cora,\
I want everything new on the screen to land in one frontend,\
so that a change to the screen is made once and the other one cannot fall behind.

## Purpose

What cora is used through, and the command that starts it: one screen, served with the
API from one process, and one documented way to reach it.

## ADDED Requirements

### Requirement: cora is used through one screen

The system SHALL serve its page and its API from one process, SHALL start that process
from the single command the documentation gives, and SHALL hold no second frontend — not
beside it as a choice, and not in the tree as code nobody runs.

#### Scenario: The documented start command starts the shell

- **WHEN** the command the quick start gives is run
- **THEN** the React shell serves the page and the API from one process

#### Scenario: There is one way to run cora

- **WHEN** the repository's run commands are listed
- **THEN** exactly one of them starts a frontend, and it is that shell

#### Scenario: No code reaches for the frontend that was removed

- **WHEN** the shipped code, the tests and the tooling are read
- **THEN** nothing imports Streamlit, and the check names any file that does

#### Scenario: The page is built before it is served

- **GIVEN** a change to the page's source
- **WHEN** the start command is run
- **THEN** the page it serves is built from that source rather than a stale build

### Requirement: A command the docs give is a command the repository has

The system SHALL keep the commands its pages hand a reader true: a target named in a
page is a target the repository defines.

#### Scenario: A page names a target that exists

- **GIVEN** a page telling a reader to run a target
- **WHEN** the repository's targets are listed
- **THEN** the named target is among them

#### Scenario: A page naming a target the repository dropped fails

- **GIVEN** a page telling a reader to run a target the repository no longer defines
- **WHEN** the commands the pages give are checked
- **THEN** the check fails and names the page and the target
