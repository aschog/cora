Every item is one failing test, but unneeded tests could be cleaned. The README and the how-to carry no item: a `.md` file is
prose, held by a person reading it. The page's items are `vitest`, the rest are `pytest`.

## 1. The outer test

- [x] 1.1 **Outer.** A travel question naming no route raising a card of the search's own
      fields, no search run, and the submitted values priced —
      `tests/acceptance/test_cards.py`

## 2. The card shape

- [x] 2.1 A card carrying a prompt, its fields and its actions
- [x] 2.2 A field carrying its name, its schema, a known value and whether it is writable
- [x] 2.3 An action carrying its label, its note and whether it waits for the fields
- [x] 2.4 A card with no action refused, because a card nobody can leave is not one
- [x] 2.5 `Pending` carrying one card, whatever stopped the turn

## 3. A decision is a card

- [x] 3.1 A decision's card carrying no fields and one action per option
- [x] 3.2 A decision with no decline still carrying the way out it is given
- [x] 3.3 An option's note reaching the action that carries it

## 4. A proposal is a card

- [x] 4.1 A proposal's card carrying the tool and every argument as read-only fields
- [x] 4.2 A proposal's card carrying an approve action and a decline action
- [x] 4.3 An argument that is not a string drawn as the JSON it arrived as

## 5. Settling carries the values

- [x] 5.1 The `Pause` port handed the action taken and the record written
- [x] 5.2 A turn resumed on a record continuing with exactly those values
- [x] 5.3 An action of no fields settling on the action alone
- [x] 5.4 An approval still bound to its own call, so two effects cannot settle each other

## 6. The wire

- [x] 6.1 A paused turn's payload carrying the card, its fields and its actions
- [x] 6.2 `POST /api/resume` taking the action and the record, and continuing the turn
- [x] 6.3 `GET /api/pending` answering with the card a reload has to draw
- [x] 6.4 A resume naming an action the card does not offer refused, rather than read as a decline
- [x] 6.5 A value for a field the card marked read-only dropped before the run sees it

## 7. The renderer

- [x] 7.1 A card of three fields and one action drawn as three controls and one button
- [x] 7.2 A card of no fields drawn as buttons alone
- [x] 7.3 A string of format `date` drawn as a date control
- [x] 7.4 A schema of three enumerated values drawn as those three and no free text
- [x] 7.5 An integer schema drawn as a number control
- [x] 7.6 A schema the lookup has no row for drawn as text
- [x] 7.7 An action that waits untakeable while a required field is empty
- [x] 7.8 That same action takeable once every required field holds a value
- [x] 7.9 An action that waits for nothing takeable on an empty card
- [x] 7.10 A settled card saying which action was taken, where it stood
- [x] 7.11 A card whose prompt and labels carry markup drawing it as written text
- [x] 7.12 A decision's card still answered by picking, and still reopenable by *Change*
- [x] 7.13 A proposal's card still showing its arguments, and none of them writable

## 8. Travel asks for its trip

- [x] 8.1 A search told no route raising a card of the search's own schema
- [x] 8.2 That card raised before any request reaches the service
- [x] 8.3 A search told a route and a window running without raising a card
- [x] 8.4 The submitted values reaching the query the service is sent

## 10. Offered as a tool that asks

- [x] 10.1 A gathering tool offered with no required arguments
- [x] 10.2 The registered schema untouched, and not the same dict as the offered one
- [x] 10.3 A tool that gathers nothing offered with its required list intact
- [x] 10.4 The runtime still refusing a gathering call missing a required argument
- [x] 10.5 The gate still raising the card for a call made with no arguments at all
- [x] 10.6 The real assembly offering `search_flights` with nothing required
- [x] 10.7 The travel instructions never ordering a route, dates or a budget asked in prose
- [x] 10.8 The instructions sending the searches at a trip being planned, not at a price
- [x] 10.9 Neither search's description telling the model to settle values before calling
- [x] 10.11 The rules saying an empty search ends only the reading, never the turn
- [ ] 10.10 **Manual, Phase 4.** A real model in the travel scope stopping on the card
      for "I want to go to Madrid" rather than answering with questions — asked in a
      *fresh* conversation, because a thread that already answered in prose teaches
      itself to keep doing it

## 9. Done

- [x] 9.1 The domain class diagram regenerated, and its guard green
- [x] 9.2 The round diagram regenerated, and its guard green
- [x] 9.3 The outer test passing
