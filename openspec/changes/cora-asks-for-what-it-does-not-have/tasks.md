Every item is one failing test. The README and the two understanding pages carry no
item: a `.md` file is prose, held by a person reading it. The model is stubbed
throughout, as the boundary it is — the last item is the one that is not.

## 1. The outer test

- [x] 1.1 **Outer.** A turn needing four values cora does not hold stopping on a card of
      them, nothing else run, and the answer resting on what the reader wrote —
      `tests/acceptance/test_ask_user.py`

## 2. The ask, as the model writes it

- [x] 2.1 An ask of three fields read as a card of three fields under its prompt
- [x] 2.2 A field's description, type, `format` and choices reaching that field's schema
- [x] 2.3 A field the ask marks required carried as required on the card
- [x] 2.4 A card offering a way out that submits nothing, beside the one that submits
- [x] 2.5 An ask naming no field refused to the model, with no card put up
- [x] 2.6 An ask whose field has no name refused the same way
- [x] 2.7 An ask naming a type cora does not read refused rather than drawn as nothing
- [x] 2.8 Two fields of one name refused, rather than one of them silently dropped

## 3. What the reader writes settles it

- [x] 3.1 The written values reaching the model as that call's own result
- [x] 3.2 A reader who writes nothing settling the ask, and the model told plainly
- [x] 3.3 A value for a field the card never put up dropped before the model is told
- [x] 3.4 The trace saying what was asked for and which fields came back filled

## 4. One fork a turn, and a form as often as the budget allows

- [x] 4.1 A second form in one round refused rather than stopping the reader twice
- [x] 4.2 A second fork still refused, where a second form is not
- [x] 4.3 A round asking for values and calling a tool settling the ask before the tool
- [x] 4.4 A form asked with the rounds spent ending the turn like any other tool
- [x] 4.5 A round asking both ways putting the form, so no fork is put twice

## 4a. A card that is not filled in is not sent

- [x] 4a.1 A box the reader left blank absent from what the model is told and the trace
- [x] 4a.2 A blank never written over the argument the model supplied — the gate's cards
- [x] 4a.3 A required field holding only spaces still holding the submit action shut —
      `PauseCard.test.tsx`

## 5. Cora's own

- [x] 5.1 The real assembly offering the tool with no plugin loaded at all
- [x] 5.2 The two asking tools describing different cases, so neither reads as the other
- [x] 5.3 The gathering ask's name reserved, so no plugin can register over it
- [x] 5.4 The brief carrying a rule for the form, as it does for every other tool

## 6. Done

- [x] 6.1 The outer test passing with its `xfail` marker gone
- [ ] 6.2 **Manual, Phase 4.** A real model stopping on a card for "I want to go to
      Madrid" rather than answering with questions — in a *fresh* conversation, because
      a thread that already answered in prose teaches itself to keep doing it
