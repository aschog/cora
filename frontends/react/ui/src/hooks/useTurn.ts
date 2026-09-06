import { useRef, useState } from 'react'
import type { Dispatch, RefObject, SetStateAction } from 'react'
import * as cora from '../api'
import type { Step } from '../api'
import type { Entry } from '../entry'
import { answeredIn, carded, openedBy, parkedOn, takenAt } from '../entry'
import { message } from '../fail'
import { forget, stow } from '../parked'
import type { Load } from './useConversation'
import type { Read } from './useSource'

/** What a different pick asks for, once the turn that raised the question has moved on. */
const correction = (label: string) => `Use ${label} instead.`

/** Taking a turn: asking one, settling a card it stopped on, and everything the page
 *  says while it runs. The spine of the page rather than a rail — it writes to the
 *  conversation, the picker, the source panel and the rails' own listings, so what it
 *  writes to is handed in.
 */
export function useTurn({
  thread,
  here,
  loads,
  setEntries,
  recall,
  pin,
  held,
  named,
  setAnswered,
  setRead,
  setTab,
  refresh,
}: {
  thread: string
  here: RefObject<string>
  loads: RefObject<number>
  setEntries: Dispatch<SetStateAction<Entry[]>>
  recall: (thread_id: string) => Promise<Load>
  pin: string | null
  held: (thread_id: string) => Promise<void>
  /** This conversation now exists in the store. Only an answer records one — a turn that
   *  paused is parked nowhere and a turn that failed is recorded nowhere — so this is the
   *  moment it becomes something to name, link to and come back to. */
  named: (thread_id: string) => void
  setAnswered: Dispatch<SetStateAction<string | null>>
  setRead: Dispatch<SetStateAction<Read | null>>
  setTab: (tab: 'STEPS') => void
  refresh: () => Promise<void>
}) {
  /* The turn being asked, and the conversation it is being asked in. Not one of
     `entries`: those are the turns the store has, and a reopen replaces them wholesale —
     which used to take the question the reader had just asked with it. */
  const [flight, setFlight] = useState<{ thread: string; entry: Entry } | null>(null)
  /* The steps of the turn being taken, and the conversation they are being taken in: a
     plan belongs to the conversation whose question it answers, so a reader who has moved
     on is simply not shown it — rather than the panel being cleared, which loses it for
     the reader who comes back while it is still running. */
  const [live, setLive] = useState<{ thread: string; steps: Step[] } | null>(null)
  /* Separate from `live`, which is a panel's contents: a conversation left behind is not
     shown the steps of the turn it left, while that request is still the one request cora
     is answering. One value cannot say both. */
  /** Which conversation cora is working in, if any. `asking` alone could not say: a
   *  resume has no entry in flight to name the thread, and the note about a question
   *  left running is only true when the work is somewhere else. */
  const [working, setWorking] = useState<string | null>(null)
  /* Separate from `trouble`, which is about a load of this page and is cleared by the
     next one that goes through: a turn asked in a conversation the reader has left is
     recorded nowhere when it fails, so this is the only place it exists — and it stands
     until they ask their next question. */
  const [lost, setLost] = useState<{ thread: string; said: string } | null>(null)
  const asked = useRef(0)

  /** The question joins the thread the moment it is asked, so it is on the page while
   *  the answer is being written; what comes back takes its place rather than following
   *  it. */
  const ask = async (question: string) => {
    const on = thread
    const from = loads.current
    const taken: Step[] = []
    /* The answer as it is being written. A model may write an aside before calling a
       tool, and that aside is the trace's, kept as the step's own detail — so the stream
       marks it and the page drops it, rather than reading round boundaries off the shape
       of the steps. */
    let written = ''
    setWorking(on)
    setLost(null)
    setLive({ thread: on, steps: taken })
    setTab('STEPS')
    const id = ++asked.current
    setFlight({
      thread: on,
      entry: { id, question, citations: [], trace: [], pending: true },
    })
    try {
      const reply = await cora.ask(
        question,
        thread,
        (step) => {
          taken.push(step)
          setLive({ thread: on, steps: [...taken] })
        },
        (piece) => {
          written += piece
          setFlight((running) =>
            running?.entry.id === id
              ? { ...running, entry: { ...running.entry, answer: written } }
              : running,
          )
        },
        /* Back to `Working…` for the rest of the tool round: what was written is no
           longer an answer, and a superseded sentence left in the answer's place is one
           cora never gave — the last thing the reader is told if the turn then fails. */
        () => {
          written = ''
          setFlight((running) =>
            running?.entry.id === id
              ? { ...running, entry: { ...running.entry, answer: undefined } }
              : running,
          )
        },
        pin,
      )
      if (cora.paused(reply)) {
        // The turn is on the page now rather than in flight: it is waiting on the
        // reader, and what they answer lands on it where it stands.
        if (parkedOn(reply)) {
          stow(on)
          if (here.current === on) {
            setEntries((said) => [
              ...said,
              carded({ id, question, citations: [], trace: taken }, reply),
            ])
          }
        }
        return
      }
      // Nothing lands on a conversation the reader left — that turn is another
      // conversation's work now. The panels follow for the same reason; an answer that
      // cites nothing leaves the panel on the document last read, which says it is not
      // cited in this answer — rather than emptying it and saying nothing at all.
      if (here.current === on) {
        // The store has this turn as of now, so appending is right unless the
        // conversation was reloaded under the reader while it ran — then its own list is
        // already on the page and appending to it would show the turn twice. Where that
        // re-read is the one thing that cannot be drawn, the turn in hand is what the page
        // has, and it is better on the page than nowhere.
        // A re-read is awaited, and the reader can leave while it runs — so where the
        // turn in hand is what lands, it lands only if they are still in that
        // conversation.
        if (loads.current === from) {
          setEntries((said) => [...said, { id, question, ...reply }])
        } else if ((await recall(on)) !== 'drawn' && here.current === on) {
          setEntries((said) => [...said, { id, question, ...reply }])
        }
        setRead((current) => openedBy(reply) ?? current)
        setAnswered((standing) => answeredIn(reply) ?? standing)
        /* Asked again rather than taken from the check above: the re-read is awaited, and
           the reader can leave while it runs. The address names the conversation they are
           in, so writing this one's into it would take them back to a conversation they
           left — which is the one thing the guards around a landing reply exist to stop. */
        if (here.current === on) named(on)
      }
    } catch (failed) {
      // A failure is recorded nowhere, so it exists only on the page it was asked from —
      // and where that page has been left, in the one line that says the answer the
      // reader was told to wait for is not coming.
      // Where the reader is still in that conversation, the failure goes where the answer
      // would have been — and it is remembered either way, because a load already on the
      // wire replaces those turns when it lands and takes the failure with it. Which of
      // the two the reader sees is one question, asked once, when the page is drawn.
      if (here.current === on) {
        setEntries((said) => [
          ...said,
          { id, question, error: message(failed), citations: [], trace: taken },
        ])
      }
      setLost({ thread: on, said: `In the conversation you left: ${message(failed)}` })
    } finally {
      setFlight((running) => (running?.entry.id === id ? null : running))
      setWorking(null)
      setLive(null)
      refresh()
      /* What the thread holds, not what was sent: a turn that was admitted fixes the pin
         even if the answer then failed, and a turn refused on the way in fixes nothing.
         Only the thread knows which happened, so the control is drawn from it. */
      void held(on)
    }
  }

  /** A card answered, either kind. The turn is already on the page, so the rest of it
   *  lands on the entry that raised the card rather than after it.
   *
   *  One function over both, because everything but the request and the two fields the
   *  card holds is the same work: the steps go to the plan, the prose lands on the
   *  entry, a second pause puts a second card up, and a failure leaves the card as it
   *  was so the reader can answer again.
   *
   *  @param answering The turn with this card marked answered. Applied before the
   *    request goes out, so the card reads as answered while cora works.
   *  @param reopening The turn with it back to waiting, applied if the request fails —
   *    its own function rather than a mirror of `answering`, because only the caller
   *    knows which of possibly several cards it just answered.
   *  @param carry The request itself, handed the three readers a streamed turn wants.
   */
  const settle = async (
    entry: Entry,
    answering: (found: Entry) => Entry,
    reopening: (found: Entry) => Entry,
    carry: (
      onStep: (step: Step) => void,
      onText: (piece: string) => void,
      onAside: () => void,
    ) => Promise<cora.Reply>,
  ) => {
    const on = thread
    const taken: Step[] = []
    let written = ''
    /* Nothing lands on a conversation the reader left. Ids repeat across
       conversations — every reopened thread numbers its turns from -1 — so an entry
       matched by id alone could be somebody else's turn entirely. */
    const at = (change: (found: Entry) => Entry) => {
      if (here.current !== on) return
      setEntries((said) =>
        said.map((each) => (each.id === entry.id ? change(each) : each)),
      )
    }
    setWorking(on)
    setLive({ thread: on, steps: taken })
    setTab('STEPS')
    at((found) => ({
      ...answering(found),
      changing: undefined,
      pending: true,
      error: undefined,
    }))
    try {
      const reply = await carry(
        (step) => {
          taken.push(step)
          setLive({ thread: on, steps: [...taken] })
        },
        (piece) => {
          written += piece
          at((found) => ({ ...found, answer: written }))
        },
        () => {
          written = ''
          at((found) => ({ ...found, answer: undefined }))
        },
      )
      if (cora.paused(reply)) {
        if (parkedOn(reply)) {
          at((found) => ({ ...carded(found, reply), pending: false }))
        }
        return
      }
      forget()
      at((found) => ({ ...found, ...reply, pending: false }))
      if (here.current === on) {
        setRead((current) => openedBy(reply) ?? current)
        setAnswered((standing) => answeredIn(reply) ?? standing)
        named(on)
      }
    } catch (failed) {
      /* Nothing was settled, so the card says nothing was: it goes back to waiting and
         the stow stays, which is what lets the reader answer again. */
      at((found) => ({
        ...reopening(found),
        error: message(failed),
        pending: false,
      }))
    } finally {
      setWorking(null)
      setLive(null)
      refresh()
    }
  }

  /** One card settled, named by where it stands on the turn, so a round that stopped
   *  twice cannot have one card answered by the other's action. */
  const answer = (
    entry: Entry,
    at: number,
    action: cora.Offered,
    values: Record<string, unknown>,
  ) =>
    settle(
      entry,
      (found) => ({ ...found, cards: takenAt(found, at, action) }),
      (found) => ({ ...found, cards: takenAt(found, at) }),
      (onStep, onText, onAside) =>
        cora.resume(thread, action.answer, values, onStep, onText, onAside),
    )

  /** An action taken. On a card still waiting it finishes the turn; on one the reader
   *  put back up it asks a new question, because the turn that raised it has already
   *  gone on and what it did cannot be taken back. */
  const take = (
    entry: Entry,
    at: number,
    action: cora.Offered,
    values: Record<string, unknown>,
  ) => {
    if (entry.changing !== at) {
      void answer(entry, at, action, values)
      return
    }
    setEntries((said) =>
      said.map((each) =>
        each.id === entry.id ? { ...each, changing: undefined } : each,
      ),
    )
    if (action.answer !== null) void ask(correction(action.label))
  }

  const change = (entry: Entry, at: number) =>
    setEntries((said) =>
      said.map((each) => (each.id === entry.id ? { ...each, changing: at } : each)),
    )

  return { flight, live, working, lost, setLost, ask, take, change }
}
