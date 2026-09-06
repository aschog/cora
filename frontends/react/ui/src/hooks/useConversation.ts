import { useRef, useState } from 'react'
import * as cora from '../api'
import type { Session, Turn } from '../api'
import type { Entry } from '../entry'
import { carded, parkedOn, recorded, unanswered } from '../entry'
import { aborted, message } from '../fail'
import { forget, forgetIf, stow, stowed } from '../parked'
import { threadInUrl } from '../route'
import { useOneAtATime } from './useOneAtATime'

/** What became of a load: drawn on the page, dropped for a later one (or a store that
 *  could not be read, which says so itself), or read and undrawable. */
export type Load = 'drawn' | 'dropped' | 'unreadable'

const newThread = () =>
  globalThis.crypto?.randomUUID?.() ?? String(Math.random()).slice(2)

/** Which conversation the page is in and which turns it shows — and every way of
 *  changing that: reading one back, starting a fresh one, deleting one, and picking up
 *  the card a paused one was left on.
 *
 *  What a load *else* changes — the panel that was reading a document, the field the
 *  picker shows — is passed in at the call site rather than wired in here, so this hook
 *  can be built before the ones that own those.
 */
export function useConversation(setTrouble: (said: string | null) => void) {
  /* Where the page opens: the conversation a card was left open in, else the one the
     address names, else a fresh one. Read as this state's first value rather than set
     from an effect — a thread minted only to be replaced on the next render is one every
     read that ran in between belongs to.
     The stow outranks the address, though the address is the more deliberate of the two,
     because of what each costs when it loses. A conversation named in the address is
     listed under SESSIONS and is one click away. A thread parked on its first question
     has answered nothing, is listed nowhere, and is reachable by this and by nothing
     else — so passing it over is not choosing between two routes, it is closing the only
     one. Whichever wins, opening it writes the address, so the two agree afterwards. */
  const [thread, setThread] = useState<string>(
    () => stowed() ?? threadInUrl() ?? newThread(),
  )
  const [entries, setEntries] = useState<Entry[]>([])
  /* Which conversation the reader is in, written where it changes rather than during a
     render: `setThread` schedules a render, so a ref assigned while rendering still
     names the old thread for anything that runs before that render lands — which is any
     reply arriving in the same task batch as the reopen. */
  const here = useRef(thread)
  /* How many conversations the page has set about loading. It names the one the reader
     is waiting for, and it tells a turn whether the entry it belongs to is still there
     to land on. */
  const loads = useRef(0)
  /* Two reads, called off separately: opening a conversation reads its turns and then
     what it is parked on, and a reader who opens another wants both of the first
     abandoned — but the second only starts once the first has landed. */
  const reading = useOneAtATime()
  const asking = useOneAtATime()

  /** Where the reader is, before a load that is about to put them there has landed: the
   *  reads that follow it guard on this, and a card picked up on mount has no other way
   *  to say which conversation it belongs to. */
  const enter = (thread_id: string) => {
    here.current = thread_id
    setThread(thread_id)
  }

  /** A conversation read from the store, applied only while it is still the one the
   *  reader is waiting for. Every load is a race with them: they can open another
   *  conversation while this one is in flight, or the same one again — and the response
   *  that arrives last is not the conversation they asked for last. */
  const loaded = async (
    thread_id: string,
    apply: (kept: Turn[]) => void,
  ): Promise<Load> => {
    const wanted = ++loads.current
    let kept: Turn[]
    try {
      kept = await cora.turns(thread_id, reading())
    } catch (failed) {
      // A load that lost the race has nothing to say either: its failure is about a
      // conversation that is not on the page. Reported from the read alone, so a failure
      // inside `apply` is not dressed up as the store being unreachable — and never for a
      // read this page called off, which is the reader moving on rather than a store that
      // cannot be reached.
      if (loads.current === wanted && !aborted(failed)) setTrouble(message(failed))
      return 'dropped'
    }
    if (loads.current !== wanted) return 'dropped'
    try {
      apply(kept)
    } catch {
      // The read went through and what came back cannot be drawn. Whether that is worth a
      // sentence is the caller's to say: a reader who clicked a conversation is owed one,
      // and a turn that re-read its own conversation has the answer in hand instead.
      return 'unreadable'
    }
    return 'drawn'
  }

  const recall = (thread_id: string) =>
    loaded(thread_id, (kept) => setEntries(recorded(kept)))

  /** Starting over is a conversation the store is not asked for: it enters the same race
   *  as every load, so a reopen already in flight loses it rather than landing on top of
   *  the new session and taking the reader back.
   *
   *  @param canLeave Whether there is a conversation to leave at all.
   *  @param leaving What else the conversation being left takes with it.
   */
  const start = ({
    canLeave,
    leaving,
  }: {
    canLeave: boolean
    leaving: () => void
  }) => {
    /* The card belonged to the conversation being left, so the page must not be put
       back into it by the next reload. */
    forget()
    if (!canLeave) return
    loads.current++
    enter(newThread())
    setEntries([])
    leaving()
  }

  /** Three things at once — which thread the page is in, which turns it shows, which
   *  document it reads — so the turns are drawn first: what cannot be drawn moves none of
   *  it, rather than leaving the reader in one conversation looking at another's.
   *
   *  @param entering What else the conversation being opened brings with it, applied in
   *    the same step as its turns.
   */
  const reopen = (session: Session, entering: (kept: Turn[]) => void) =>
    loaded(session.thread_id, (kept) => {
      const turns = recorded(kept)
      enter(session.thread_id)
      setEntries(turns)
      entering(kept)
    })

  /** What a conversation is still parked on, drawn after its turns: it is in no store,
   *  so nothing else on the page would bring it back. */
  const parked = async (thread_id: string) => {
    /* `undefined` is a read that could not be made — refused, unreachable, or called off
       because the reader opened another conversation. `null` is the store answering that
       nothing is parked. The difference is the whole of what follows: only the second is
       news about the card. */
    const waiting = await cora.pending(thread_id, asking()).catch(() => undefined)
    if (here.current !== thread_id || waiting === undefined) return
    /* Told plainly there is nothing parked — or that what is parked is not a pause this
       page can draw. Either way the stow is stale, and holding it would send every later
       reload back to a conversation with no question in it. */
    if (!parkedOn(waiting)) {
      forgetIf(thread_id)
      return
    }
    stow(thread_id)
    setEntries((said) =>
      said.some(unanswered)
        ? said
        : [
            ...said,
            carded(
              {
                id: -(said.length + 1),
                question: waiting.asked,
                citations: [],
                trace: [],
              },
              waiting,
            ),
          ],
    )
  }

  /** A conversation deleted, once the reader has said so, and the card stowed for it let
   *  go: the stow is what a reload comes back through, and a conversation that is gone is
   *  nowhere to come back to. The list is redrawn by the refresh every write here goes
   *  through. */
  const discard = (session: Session) =>
    cora.deleteSession(session.thread_id).then(() => forgetIf(session.thread_id))

  return {
    thread,
    entries,
    setEntries,
    here,
    loads,
    enter,
    recall,
    start,
    reopen,
    parked,
    discard,
  }
}
