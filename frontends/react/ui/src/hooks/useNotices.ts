import { useEffect, useRef } from 'react'
import * as cora from '../api'
import type { Conversation } from '../api'
import { showThread } from '../route'

/** How often a field is asked what it is doing. A notice says what is true now, so the
 *  screen is at most this far behind the wrist. */
const EVERY = 5000

type Props = {
  /** The fields that have a page. Only those are asked: a field with no page has nothing
   *  to put on the screen, and nothing beside the reader writes to one. */
  pages: string[]
  /** Every conversation, newest first — which is what makes the first one pinned to a
   *  field the one that field opens. */
  conversations: Conversation[]
  /** The conversation on the screen, so the one already open is not opened again. */
  here: string
}

/**
 * A field that speaks takes the screen: a notice written after the last one this saw
 * opens that field's newest conversation, wherever the reader had got to.
 *
 * What the notice *says* is never read. `{"workout":"running"}` is the fitness trainer's
 * vocabulary and no shell should know it — the rule is that a field wrote, which is a
 * field asking to be looked at, and what it meant is between it and its own page.
 *
 * The first answer from a field is a baseline rather than an event. A notice outlives the
 * page that wrote it, so the one standing at load is last time's, and acting on it would
 * drag the reader off on every reload.
 *
 * Quiet where nothing answers: a deployment in which no notice is ever written is the
 * normal one, and a poll that raised a banner would be the page complaining about a
 * feature the reader may not have.
 */
export function useNotices({ pages, conversations, here }: Props) {
  /* The last arrival seen per field. A ref and not state: nothing is drawn from it, and
     a render per poll would be a render every five seconds on every open page. */
  const seen = useRef<Record<string, number>>({})
  /* What the poll reads when it next runs, rather than what was true when the effect was
     set up — the alternative is tearing the interval down and building it again every
     time a conversation joins the list. */
  const now = useRef({ conversations, here })
  useEffect(() => {
    now.current = { conversations, here }
  }, [conversations, here])

  /* The fields as one value, so an array built fresh on every render does not restart
     the poll. */
  const asking = JSON.stringify(pages)
  useEffect(() => {
    const fields = JSON.parse(asking) as string[]
    if (fields.length === 0) return
    let stopped = false

    const ask = async () => {
      /* A tab nobody is looking at has no screen for a field to take, and the one thing
         this does with an arrival is put a conversation on that screen. The poll picks
         up where it left off when the reader comes back, and the baseline each field
         already has is what keeps the catch-up from dragging them somewhere. */
      if (document.visibilityState === 'hidden') return
      for (const field of fields) {
        const held = await cora.notice(field).catch(() => null)
        if (stopped) return
        if (held === null) continue
        /* A field nobody has written to answers with no arrival at all, and that is a
           baseline like any other — otherwise the first notice a field ever takes is the
           one this would sit through. */
        const arrived = held.at ?? 0
        const before = seen.current[field]
        seen.current[field] = arrived
        if (before === undefined || arrived <= before) continue
        const opening = now.current.conversations.find((each) => each.pin === field)
        if (opening && opening.thread_id !== now.current.here)
          showThread(opening.thread_id)
      }
    }

    void ask()
    const timer = setInterval(() => void ask(), EVERY)
    return () => {
      stopped = true
      clearInterval(timer)
    }
  }, [asking])
}
