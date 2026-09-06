As a reader,\
I want a part of the page that cannot be drawn to cost me that part,\
so that a fault in one rail does not take the conversation I am reading with it.

## Purpose

What the screen does when part of it throws while being drawn. A fault is bounded by
the column it happened in. It is said in a sentence rather than shown as an empty
window.

## ADDED Requirements

### Requirement: A part of the page that cannot be drawn is replaced by a sentence

Where a column or a panel throws while rendering, the page SHALL draw a sentence in its
place. The sentence SHALL name what could not be drawn, and SHALL replace nothing else.

#### Scenario: A panel that throws says so

- **GIVEN** a store answering with a shape the sessions panel cannot read
- **WHEN** the reader opens that panel
- **THEN** they are told that panel could not be drawn

#### Scenario: What threw is on the console

- **GIVEN** a part of the page that throws while rendering
- **WHEN** it is caught
- **THEN** the throw and the tree it came from reach the console

### Requirement: The rest of the page is still drawn

A column that could not be drawn SHALL NOT unmount the others. The conversation, the
rails and the controls outside that column remain usable.

#### Scenario: The conversation survives a broken panel

- **GIVEN** a panel that threw while being drawn
- **WHEN** the reader looks at the page
- **THEN** the conversation and the documents rail are still there

### Requirement: A panel that broke is left behind by moving to another

The strip that chooses between panels SHALL stay outside what it chooses. Moving to
another panel SHALL draw that panel rather than the sentence.

#### Scenario: Switching tabs escapes it

- **GIVEN** a panel that threw while being drawn
- **WHEN** the reader chooses another panel
- **THEN** that panel is drawn, and the sentence is gone

### Requirement: Trying again re-draws what threw

The sentence SHALL offer to draw the part again. Taking it SHALL re-draw the children
rather than reload the page.

#### Scenario: What was mended is drawn

- **GIVEN** a part of the page that threw, and has since been given something it can draw
- **WHEN** the reader tries again
- **THEN** it is drawn

#### Scenario: What still throws says so again

- **GIVEN** a part of the page that throws, and still would
- **WHEN** the reader tries again
- **THEN** they are told again that it could not be drawn
