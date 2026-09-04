Every item is one failing test. The page's items are `vitest`, the rest are `pytest`, and
the README this change touches carries no item: a `.md` file is prose, held by a person
reading it.

## 1. The outer test

- [x] 1.1 **Outer.** A conversation deleted from the list, gone from it, its turns
      unreadable and its pin dropped — the parked half is 3.3's and 5.3's, which is
      where a resume is already driven —
      `tests/acceptance/test_sessions.py::test_a_conversation_i_delete_is_gone_from_both_stores`,
      marked `@pytest.mark.xfail(strict=True)`

## 2. The record of the turns

- [x] 2.1 One thread's turns deleted, and read back as none
- [x] 2.2 The other threads' turns untouched, and still listed
- [x] 2.3 A thread nothing was recorded under deleted without complaint
- [x] 2.4 A store that cannot be written raising the failure this adapter already
      translates

## 3. The thread the model answered on

- [x] 3.1 A deleted thread holding no pin, where it was pinned before
- [x] 3.2 A deleted thread waiting on nothing, where a turn was parked in it
- [x] 3.3 Resuming a deleted thread refused as a thread waiting on nothing is
- [x] 3.4 A thread nobody has asked anything on deleted without complaint
- [x] 3.5 The same over the file-backed checkpointer, which is what a deployment deletes
      from

## 4. One call that drops both halves

- [x] 4.1 Deleting a conversation dropping its record and its thread in one call
- [x] 4.2 A drop that fails on the thread leaving the conversation listed, so deleting
      again finishes it
- [x] 4.3 A cora assembled with no place to record turns deleting without complaint

## 5. The endpoint

- [x] 5.1 `DELETE /api/sessions/{thread_id}` answering `204`, with the conversation off
      the listing
- [x] 5.2 The same request against a store that went away answering `503` and its
      sentence
- [x] 5.3 Deleting the thread a turn is parked in, then resuming it, refused

## 6. The list on the page

- [x] 6.1 Each listed conversation drawing a delete, and the request going out for the
      one clicked
- [x] 6.2 The conversation open on the page drawing none
- [x] 6.3 A conversation cora is still answering a question in drawing none
- [x] 6.4 The list redrawn after a delete, without the conversation deleted
- [x] 6.5 A delete that fails saying so, with the conversation still listed
- [x] 6.6 The card stowed for a deleted conversation let go, so a reload opens a new one

## 7. Done

- [x] 7.1 Drop 1.1's `xfail` marker and watch the outer test pass — ticked with group
      5, which is where the outer test's own surface was finished

## 8. Asked about first, drawn as an icon

Review feedback, after 7.1: a delete offered outright is one click from gone, a word per
row is noise in a narrow rail, and the memory rail was the same row with another
spelling.

- [x] 8.1 The control asking rather than deleting, with nothing asked of cora yet
- [x] 8.2 A confirmed question deleting the conversation it named
- [x] 8.3 Keeping the conversation deleting nothing, and asking again next time
- [x] 8.4 The question naming the conversation and saying what is left untouched
- [x] 8.5 Escape and the page behind the question both reading as keeping it
- [x] 8.6 The control drawn as an icon, named for the row it would delete
- [x] 8.7 The conversation being read marked in the list
- [x] 8.8 A fact forgotten by that same control, in the memory rail
