import { useState } from 'react'
import type { RefObject } from 'react'
import * as cora from '../api'
import { useOneAtATime } from './useOneAtATime'

/** Which field this conversation is fixed to, and which one its own turns were answered
 *  in. Both are the conversation's, so both are dropped when it is left — and neither is
 *  the field the rail draws, which `useRails` derives from them.
 *
 *  @param here Which conversation the reader is in, so a read that lands after they have
 *    moved on settles the picker for a thread that is no longer on the page.
 */
export function usePin(here: RefObject<string>) {
  /* `fixedPin` is whether a turn has written the pin into the thread's state — until one
     has, the pick is the reader's intention and the next question is what settles it. */
  const [pin, setPin] = useState<string | null>(null)
  const [fixedPin, setFixedPin] = useState(false)
  const [answered, setAnswered] = useState<string | null>(null)
  const reading = useOneAtATime()

  const pick = (scope: string) => {
    setPin(scope === '' ? null : scope)
    /* Asking for Chat is the reader saying no field is named, and the field a turn
       naming none runs in is the default one — so the field routing settled is news this
       outranks rather than falls back to. */
    if (scope === '') setAnswered(null)
  }

  /** Which field a reopened conversation is in. The pin outlived the page because it is
   *  the thread's own state; the picker is only where it is drawn. */
  const held = async (thread_id: string) => {
    /* A read that failed is no news about the field: `undefined` leaves the control as it
       stands, where `null` would re-open a picker on a thread the engine has closed and
       get the reader's next pick refused over a field they can no longer see. */
    const fixed = await cora.pinned(thread_id, reading()).catch(() => undefined)
    if (here.current !== thread_id || fixed === undefined) return
    setPin(fixed)
    setFixedPin(fixed !== null)
  }

  /** A conversation left behind takes its field with it. */
  const reset = () => {
    setPin(null)
    setFixedPin(false)
    setAnswered(null)
  }

  return { pin, fixedPin, answered, pick, held, reset, setAnswered }
}
