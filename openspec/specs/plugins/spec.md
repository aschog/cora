# plugins Specification

## Purpose

What gives cora a subject. A plugin contributes what cora should know, what it can do
and what it will not accept; with none loaded cora is a general assistant rather than a
specialist that was handed nothing.

## Requirements

### Requirement: A plugin contributes instructions, tools and rules

The system SHALL take from a plugin any of: instructions heading its own section of the
brief, tools the model may call, and rules that refuse an input — and SHALL accept a
plugin that brings only one of them.

#### Scenario: A plugin's contribution is live in the app

- **GIVEN** a plugin bringing instructions and a tool
- **WHEN** cora is asked a question in that subject
- **THEN** the instructions are in the brief and the tool is callable

#### Scenario: A plugin of rules alone

- **GIVEN** a plugin bringing only rules
- **WHEN** it is loaded
- **THEN** it contributes no persona and no tools, and its rules screen the input

### Requirement: cora with no plugin is a plain assistant

The system SHALL start with no plugin loaded, SHALL answer without one, and SHALL then
name no subject in its brief and refuse nothing on a plugin's behalf.

#### Scenario: A bare cora answers

- **GIVEN** an app with no plugins named
- **WHEN** a question is asked
- **THEN** it is answered, and the brief names no subject

### Requirement: Plugins compose in the order they were named

The system SHALL compose several plugins into one set, SHALL order their instructions,
tools and rules by the order they were named, and SHALL run cora's own rules before any
of theirs.

#### Scenario: A guard plugin and a subject plugin in one app

- **GIVEN** two plugins named in order
- **WHEN** a question is asked
- **THEN** both are live, their sections appear in that order, and cora's own rules ran
  first

### Requirement: A set that cannot be composed is refused before it is wired

The system SHALL refuse, when the plugins are composed rather than mid-turn, a module
named twice, a tool name that is cora's own, and one tool name offered by two plugins —
and SHALL name the module at fault.

#### Scenario: Two plugins offer one tool name

- **GIVEN** two plugins offering the same tool name
- **WHEN** the app is assembled
- **THEN** it is refused, naming the module the collision came from

#### Scenario: A plugin takes a name cora reserves

- **GIVEN** a plugin offering a tool named as one of cora's own
- **WHEN** the app is assembled
- **THEN** it is refused, naming what that name is reserved for

### Requirement: A plugin ships as its own distribution

The system SHALL name no plugin and no subject in its own package, and SHALL load a
plugin by the module path it was given.

#### Scenario: A shipped plugin loads through the registry

- **GIVEN** a plugin installed beside cora
- **WHEN** it is named to cora
- **THEN** it is discovered and loaded, and nothing in cora's own package names it
