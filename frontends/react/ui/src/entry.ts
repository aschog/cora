import type { Card, Citation, Offered, Pending, Result, Step, Turn } from './api'

/** Whether what came back is really a turn parked on a card. Typed as one, but it
 *  arrived over the network: a page that read a card off something else would draw an
 *  empty one, and stow a conversation with no question in it. */
export const parkedOn = (waiting: Pending | null): waiting is Pending => !!waiting?.card

export type Entry = {
  /** Which turn this is, so an answer lands on the question that was asked and on no
   *  other. A conversation reopened mid-turn replaces the thread wholesale, and "the
   *  last entry" is then somebody else's. */
  id: number
  question: string
  answer?: string
  error?: string
  citations: Citation[]
  trace: Step[]
  /** Asked, not yet answered: the question is on the page while cora works on it. */
  pending?: boolean
  /** What cora stopped on, in the order it stopped: a card while it is open, and
   *  afterwards the line that says what the reader did about it. A list because a round
   *  may stop twice, and the first card keeps its answer instead of being replaced by
   *  the second. */
  cards?: Shown[]
  /** Which card is back up: taking an action now asks a new question, because the turn
   *  it belonged to has already gone on. */
  changing?: number
}

/** One card a turn stopped on, and the action the reader took once they have taken one. */
type Shown = { card: Card; taken?: Offered }

/** A turn stopped on a card nobody has answered yet. Exported because the page has two
 *  things to do about one: draw the card as open, and refuse the composer — two open
 *  questions on one thread would be two answers to one turn. */
export const unanswered = (entry: Entry) =>
  (entry.cards ?? []).some((shown) => shown.taken === undefined)

/** Whether a card can be put back up. A card of no fields asked the reader to choose
 *  between values cora already had, and choosing again costs nothing; one that laid out
 *  a call or a form did something, and offering to change it would say otherwise. */
export const reopenable = (shown: Shown) => shown.card.fields.length === 0

/** The turn with the card it has just stopped on put on it. Appended, because a round
 *  may stop twice: the answer to the first is the record of what cora was allowed to do,
 *  and replacing it would lose that and leave the second unanswerable. Read in one
 *  place, so the three sites that put a card on the page cannot disagree. */
export const carded = (found: Entry, waiting: { card: Card }): Entry => ({
  ...found,
  cards: [...(found.cards ?? []), { card: waiting.card }],
})

/** This turn's cards with the one at `at` answered, or put back to waiting. */
export const takenAt = (found: Entry, at: number, taken?: Offered) =>
  (found.cards ?? []).map((shown, index) =>
    index === at ? { ...shown, taken } : shown,
  )

/** A conversation's recorded turns. Numbered apart from the ones this page asked, so
 *  a reply still in flight can never match one of them. */
export const recorded = (kept: Turn[]): Entry[] =>
  kept.map((turn, n) => ({
    id: -(n + 1),
    question: turn.question,
    ...turn.result,
  }))

/** The turn the panels speak for: the newest one that actually answered. A turn that
 *  failed carries no citations and never will, so reading it as "this answer" takes the
 *  marks off the answer the reader is still reading. */
export const answering = (entries: Entry[]): Entry | undefined =>
  entries.filter((entry) => !entry.error).at(-1)

/** The one field a turn was answered in, or nothing where it named none or several —
 *  the rail draws one field, and a turn under two is not a turn it can follow. */
export function answeredIn(reply: { scopes?: string[] }): string | null {
  return reply.scopes?.length === 1 ? reply.scopes[0] : null
}

/** The document an answer opens on: its first citation, in the field that citation was
 *  cut from. An answer that cited nothing leaves whatever was open. */
export function openedBy(reply: Result): { document: string; scope: string } | null {
  const [first] = reply.citations
  return first ? { document: first.document, scope: first.scope } : null
}

/** The documents this conversation has actually rested on, by name. */
export function citedDocuments(entries: Entry[], field: string): Set<string> {
  /* Per field, because the rail lists one: a document of this name cited in another
     field is not this field's document, and offering it would open the wrong text. */
  return new Set(
    entries.flatMap((entry) =>
      entry.citations
        .filter((citation) => citation.scope === field)
        .map((citation) => citation.document),
    ),
  )
}

export function lastTrace(entries: Entry[]): Step[] {
  return entries.length ? entries[entries.length - 1].trace : []
}
