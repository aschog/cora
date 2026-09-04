import { useCallback, useEffect, useRef, useState } from 'react'
import * as cora from './api'
import type {
  Citation,
  Decision,
  Fact,
  Proposal,
  Result,
  Session,
  Step,
  Turn,
} from './api'
import Answer from './components/Answer'
import CitationModal from './components/CitationModal'
import DocumentRail from './components/DocumentRail'
import NewSession from './components/NewSession'
import RailToggle from './components/RailToggle'
import ScopePicker from './components/ScopePicker'
import MemoryPanel from './components/MemoryPanel'
import PlanPanel from './components/PlanPanel'
import SessionsPanel from './components/SessionsPanel'
import SourcePanel from './components/SourcePanel'
import type { Notice } from './components/UploadNotice'

const TABS = ['PLAN', 'SOURCE', 'SESSIONS', 'MEMORY'] as const
type Tab = (typeof TABS)[number]

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
  /** The question cora stopped on: a card while it is open, and afterwards the line that
   *  says what it settled. */
  decision?: Decision
  /** What the reader picked — `null` is choosing none of them. Absent is a card still
   *  waiting on them. */
  chosen?: string | null
  /** The effects this turn proposed, in the order it proposed them. A list because a
   *  round may ask for two, while it may ask the reader at most one question — so the
   *  first of them keeps its answer instead of being replaced by the second. */
  proposals?: Waiting[]
  /** The card put back up: picking now asks a new question, because the turn it belonged
   *  to has already gone on. */
  changing?: boolean
}

const PARKED = 'cora.parked'
/** Which conversation a card was left open in. A reload mints a new thread, and a paused
 *  turn is in no store — so without this the question would be unreachable: SESSIONS
 *  lists only conversations that have answered something. */
const stow = (thread_id: string) => keep(PARKED, thread_id)
const forget = () => keep(PARKED, null)
/** Only this conversation's own card is forgotten. A thread parked on its *first*
 *  question is recorded nowhere and listed under no session, so clearing the stow while
 *  reading a different conversation would leave that card reachable by no route at all. */
const forgetIf = (thread_id: string) => {
  if (stowed() === thread_id) forget()
}

const keep = (name: string, value: string | null) => {
  try {
    if (value === null) globalThis.sessionStorage?.removeItem(name)
    else globalThis.sessionStorage?.setItem(name, value)
  } catch {
    /* A browser that keeps nothing for this page. The card is then a reload away from
       gone, which is what it was before it could be kept at all. */
  }
}

const stowed = () => {
  try {
    return globalThis.sessionStorage?.getItem(PARKED) ?? null
  } catch {
    return null
  }
}

/** What a different pick asks for, once the turn that raised the question has moved on. */
const correction = (label: string) => `Use ${label} instead.`

/** One effect a turn proposed, and the reader's answer once they have given it. */
export type Waiting = { proposal: Proposal; approved?: boolean }

/** A turn stopped on a card nobody has answered yet, whichever kind it is. Exported
 *  because the page has two things to do about one: draw the card as open, and refuse
 *  the composer — two open questions on one thread would be two answers to one turn. */
export const unanswered = (entry: Entry) =>
  (!!entry.decision && entry.chosen === undefined) ||
  (entry.proposals ?? []).some((each) => each.approved === undefined)

/** Whether a parked turn carries anything to draw a card from, however it arrived. */
const stops = (waiting: cora.Pending) => !!(waiting.decision || waiting.proposal)

/** The turn with the card it has just stopped on put on it. A decision replaces the one
 *  before it, because a turn may ask the reader at most once. A proposal is appended,
 *  because a round may propose two: the answer to the first is the record of what cora
 *  was allowed to do, and replacing it would lose that and leave the second unanswerable.
 *  Read in one place, so the three sites that put a card on the page cannot disagree. */
const carded = (found: Entry, waiting: cora.Pending): Entry =>
  waiting.decision
    ? { ...found, decision: waiting.decision, chosen: undefined }
    : waiting.proposal
      ? {
          ...found,
          proposals: [...(found.proposals ?? []), { proposal: waiting.proposal }],
        }
      : found

/** This turn's proposals with the one call named answered, or put back to waiting. */
const answeredAt = (found: Entry, call: string, approved?: boolean) =>
  (found.proposals ?? []).map((each) =>
    each.proposal.call_id === call ? { ...each, approved } : each,
  )

const UNDRAWABLE = 'That conversation could not be read.'

/** One line the page says about itself, and which of them it is. */
type Banner = { which: string; said: string }

/** What became of a load: drawn on the page, dropped for a later one (or a store that
 *  could not be read, which says so itself), or read and undrawable. */
type Load = 'drawn' | 'dropped' | 'unreadable'

const newThread = () =>
  globalThis.crypto?.randomUUID?.() ?? String(Math.random()).slice(2)

export default function App() {
  const [tab, setTab] = useState<Tab>('PLAN')
  const [thread, setThread] = useState<string>(newThread)
  const [entries, setEntries] = useState<Entry[]>([])
  /* The turn being asked, and the conversation it is being asked in. Not one of
     `entries`: those are the turns the store has, and a reopen replaces them wholesale —
     which used to take the question the reader had just asked with it. */
  const [flight, setFlight] = useState<{ thread: string; entry: Entry } | null>(null)
  const [documents, setDocuments] = useState<string[]>([])
  /* The fields this deployment offers, and the one this conversation is fixed to.
     `fixedPin` is whether a turn has written it into the thread's state — until one has,
     the pick is the reader's intention and the next question is what settles it. */
  const [fields, setFields] = useState<string[]>([])
  const [pin, setPin] = useState<string | null>(null)
  const [fixedPin, setFixedPin] = useState(false)
  /* The field a question belonging to none is answered in, and where an upload naming
     none lands. The server's answer rather than a constant here: it is one fact, and
     the page is not where it is decided. */
  const [anyField, setAnyField] = useState('')
  /* The field this conversation's own turns were answered in. The conversation's, so it
     is dropped when it is left. */
  const [answered, setAnswered] = useState<string | null>(null)
  const [facts, setFacts] = useState<Fact[]>([])
  const [sessions, setSessions] = useState<Session[]>([])
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
  const [read, setRead] = useState<{ document: string; scope: string } | null>(null)
  const [opened, setOpened] = useState<Citation | null>(null)
  const [trouble, setTrouble] = useState<string | null>(null)
  /* What the last upload did. Its own state, because it is not trouble and a refresh
     going through does not take it away: a duplicate upload is answered with `0` chunks,
     and saying nothing about it reads the same as success and the same as nothing
     happening. Moving to another conversation does end it — it is news about the desk the
     reader was at. */
  const [notice, setNotice] = useState<Notice | null>(null)
  /* Separate from `trouble`, which is about a load of this page and is cleared by the
     next one that goes through: a turn asked in a conversation the reader has left is
     recorded nowhere when it fails, so this is the only place it exists — and it stands
     until they ask their next question. */
  const [lost, setLost] = useState<{ thread: string; said: string } | null>(null)
  const [leftOpen, setLeftOpen] = useState(true)
  const asked = useRef(0)
  /* How many conversations the page has set about loading. It names the one the reader
     is waiting for, and it tells a turn whether the entry it belongs to is still there
     to land on. */
  const loads = useRef(0)
  /* Which conversation the reader is in, written where it changes rather than during a
     render: `setThread` schedules a render, so a ref assigned while rendering still
     names the old thread for anything that runs before that render lands — which is any
     reply arriving in the same task batch as the reopen. */
  const here = useRef(thread)
  /* Which field the newest documents load asked about, so an older one cannot land. */
  const shown = useRef('')
  const [rightOpen, setRightOpen] = useState(true)

  /* Where the rail sits when nothing else has spoken. One field loaded is a field
     routing cannot choose against, so every turn runs in it; with more than one, a turn
     belonging to none is answered in the default field. */
  const home = fields.length === 1 ? fields[0] : anyField

  /** Which field the rail shows and uploads into, in one expression rather than in the
   *  several places that used to write it — a pin outranks the conversation's own turns
   *  because a pinned conversation has one field for good, and a conversation that has
   *  said nothing sits at home. Derived, so nothing can race it: every writer below
   *  settles one of the inputs and none settles the answer. */
  const field = pin ?? answered ?? home

  /** What the page shows around the conversation, loaded together: one banner for all
   *  of it, and a load that goes through clears the last one's. Loading the badge on
   *  its own raced that banner — a page that could not find out which plugin is loaded
   *  would say `bare cora` and then clear the only warning that it was guessing. */
  const refresh = useCallback(
    () => {
      const asked = field
      shown.current = asked
      return Promise.all([
        cora.documents(field),
        cora.memory(),
        cora.sessions(),
        cora.scopes(),
      ])
        .then(([indexed, kept, before, offered]) => {
          /* The listing is per field and this load asked for the field the page was in
             when it started. A load the reader has moved past answers about a field the
             rail is no longer showing: its list must not land under the new one's name,
             and neither must its news — clearing the banner would hide a failure the
             field on the page is still in, and raising one would report a field that is
             no longer drawn. The same race every other read here guards against. */
          if (shown.current !== asked) return
          setDocuments(indexed)
          setFacts(kept)
          setSessions(before)
          setFields(offered.available)
          setAnyField(offered.default)
          setTrouble(null)
        })
        .catch((failed) => {
          if (shown.current === asked) reportTo(setTrouble)(failed)
        })
    },
    [field],
  )

  useEffect(() => {
    refresh()
  }, [refresh])

  /* A card left open outlives the page it was drawn on: the conversation it was open in
     is picked back up, and the question with it. */
  useEffect(() => {
    const parked = stowed()
    if (!parked) return
    here.current = parked
    setThread(parked)
    void reopen({ thread_id: parked, opened_with: '' })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  /** What the page has to say about itself, in one place: a load that failed, a question
   *  left running that will not be answered, and what became of the last upload. The
   *  second is not cleared by the next load going through, and says nothing once the
   *  reader is back in the conversation it belongs to — where the sentence would be false.
   *  What became of an upload is not here: it belongs beside the list it changed — which
   *  leaves both of these trouble, so the strip has one look rather than a tone each. */
  const banners = [
    { which: 'load', said: trouble },
    { which: 'lost', said: lost && lost.thread !== thread ? lost.said : null },
  ].filter((banner): banner is Banner => Boolean(banner.said))

  const cited = citedDocuments(entries, field)
  /** What the conversation column shows: its recorded turns, and the one being asked in
   *  it. A turn in flight elsewhere is that conversation's, and is not drawn here. */
  const conversation =
    flight?.thread === thread ? [...entries, flight.entry] : entries

  /** The document as this conversation last had it, in the field the rail is showing.
   *  A filename names nothing on its own — one name can cover a document in each field,
   *  and two uploads within one — so the newest citation for the name *here* is what
   *  says which text to read. A field the conversation has cited nothing in names
   *  nothing, which is the honest answer: this field's copy has not been read. */
  const latestFor = (opened: { document: string; scope: string }) =>
    entries
      .slice()
      .reverse()
      .flatMap((entry) => entry.citations)
      .find(
        (citation) =>
          citation.document === opened.document && citation.scope === opened.scope,
      )

  /** Where a document's text is kept: the field it was ingested into and the upload it
   *  arrived as. Both, because a span is only meaningful against one field's file. */
  const sourceOf = (opened: { document: string; scope: string }) => {
    const found = latestFor(opened)
    return found?.upload ? { scope: found.scope, upload: found.upload } : null
  }

  /** Whether there is a conversation to leave: what the header draws, and what `start`
   *  refuses on. */
  const somethingToLeave = conversation.length > 0
  const asking = working !== null

  /** Two different questions about one document. What is *marked* is what this answer
   *  rested on, or a document cited three turns ago accumulates marks until most of it
   *  is highlighted; what is *openable* is any upload the conversation still names. Both
   *  come from one citation set, because a span measured in one upload's text points at
   *  arbitrary words in another's. */
  const passagesIn = (opened: { document: string; scope: string }) => {
    const found = latestFor(opened)
    if (!found) return []
    return (answering(entries)?.citations ?? []).filter(
      (citation) =>
        citation.document === opened.document &&
        citation.upload === found.upload &&
        citation.scope === found.scope,
    )
  }

  const open = (document: string) => {
    setRead({ document, scope: field })
    setTab('SOURCE')
  }

  /** A conversation's recorded turns. Numbered apart from the ones this page asked, so
   *  a reply still in flight can never match one of them. */
  const recorded = (kept: Turn[]): Entry[] =>
    kept.map((turn, n) => ({
      id: -(n + 1),
      question: turn.question,
      ...turn.result,
    }))

  /** A conversation read from the store, applied only while it is still the one the
   *  reader is waiting for. Every load is a race with them: they can open another
   *  conversation while this one is in flight, or the same one again — and the response
   *  that arrives last is not the conversation they asked for last. */
  const loaded = async (thread_id: string, apply: (kept: Turn[]) => void): Promise<Load> => {
    const wanted = ++loads.current
    let kept: Turn[]
    try {
      kept = await cora.turns(thread_id)
    } catch (failed) {
      // A load that lost the race has nothing to say either: its failure is about a
      // conversation that is not on the page. Reported from the read alone, so a failure
      // inside `apply` is not dressed up as the store being unreachable.
      if (loads.current === wanted) setTrouble(message(failed))
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
    setTab('PLAN')
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
        if (stops(reply)) {
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
        setRead((current) => _opened(reply) ?? current)
        setAnswered((standing) => answeredIn(reply) ?? standing)
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

  /** Starting over is a conversation the store is not asked for: it enters the same race
   *  as every load, so a reopen already in flight loses it rather than landing on top of
   *  the new session and taking the reader back. */
  const start = () => {
    /* The card belonged to the conversation being left, so the page must not be put
       back into it by the next reload. */
    forget()
    if (!somethingToLeave) return
    const fresh = newThread()
    loads.current++
    here.current = fresh
    setThread(fresh)
    setEntries([])
    setRead(null)
    setNotice(null)
    setPin(null)
    setFixedPin(false)
    setAnswered(null)
    refresh()
  }

  /** An upload the reader started and then left behind. Ingestion takes seconds and
   *  nothing stops them opening another conversation while it runs, so the notice is
   *  stamped with the one they started it in — news about a desk they have left is not
   *  drawn, and cannot be left standing where nothing clears it. Taking a notice *away*
   *  is stamped for the same reason: a refusal from a conversation they have left must not
   *  clear news about an upload that worked in this one. The refresh and the refusal's own
   *  sentence are not stamped — a document is added, or refused, wherever they are. */
  const uploaded = (file: File) => {
    const from = here.current
    return cora
      .upload(file, field)
      .then((added) => {
        if (here.current === from) setNotice(ingested(added))
        return refresh()
      })
      .catch((failed) => {
        if (here.current === from) setNotice(null)
        setTrouble(message(failed))
      })
  }

  const recall = (thread_id: string) =>
    loaded(thread_id, (kept) => setEntries(recorded(kept)))

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
    setTab('PLAN')
    at((found) => ({
      ...answering(found),
      changing: false,
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
        if (stops(reply)) at((found) => ({ ...carded(found, reply), pending: false }))
        return
      }
      forget()
      at((found) => ({ ...found, ...reply, pending: false }))
      if (here.current === on) {
        setRead((current) => _opened(reply) ?? current)
        setAnswered((standing) => answeredIn(reply) ?? standing)
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

  const decide = (entry: Entry, chosen: string | null) =>
    settle(
      entry,
      (found) => ({ ...found, chosen }),
      (found) => ({ ...found, chosen: undefined }),
      (onStep, onText, onAside) =>
        cora.resume(thread, chosen, onStep, onText, onAside),
    )

  /** One effect approved or declined, named by the call it answers so a round that
   *  proposed two cannot have one settled by the other's answer. There is no putting
   *  this card back up: a decision answered one way can be asked again the other, and
   *  an effect that has happened cannot be taken back. */
  const approve = (entry: Entry, call: string, yes: boolean) =>
    void settle(
      entry,
      (found) => ({ ...found, proposals: answeredAt(found, call, yes) }),
      (found) => ({ ...found, proposals: answeredAt(found, call) }),
      (onStep, onText, onAside) =>
        cora.approve(thread, call, yes, onStep, onText, onAside),
    )

  /** A pick. On a card still waiting it finishes the turn; on one the reader put back up
   *  it asks a new question, because the turn that raised it has already gone on and
   *  what it did cannot be taken back. */
  const decided = (entry: Entry, chosen: string | null) => {
    if (!entry.changing) {
      void decide(entry, chosen)
      return
    }
    setEntries((said) =>
      said.map((each) => (each.id === entry.id ? { ...each, changing: false } : each)),
    )
    if (chosen !== null) void ask(correction(chosen))
  }

  const change = (entry: Entry) =>
    setEntries((said) =>
      said.map((each) => (each.id === entry.id ? { ...each, changing: true } : each)),
    )

  /** What a conversation is still parked on, drawn after its turns: it is in no store,
   *  so nothing else on the page would bring it back. */
  const parked = async (thread_id: string) => {
    const waiting = await cora.pending(thread_id).catch(() => null)
    if (here.current !== thread_id) return
    /* A payload with nothing to settle in it is not a pause, however it arrived: the
       card is drawn from what stopped the turn or not at all. */
    if (!waiting || !stops(waiting)) {
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

  /** Three things at once — which thread the page is in, which turns it shows, which
   *  document it reads — so the turns are drawn first: what cannot be drawn moves none of
   *  it, rather than leaving the reader in one conversation looking at another's. */
  const reopen = async (session: Session) => {
    const outcome = await loaded(session.thread_id, (kept) => {
      const turns = recorded(kept)
      here.current = session.thread_id
      setThread(session.thread_id)
      setEntries(turns)
      setRead(null)
      setNotice(null)
      /* A conversation nothing pinned is still in a field: routing settled one per turn
         and the last of them is where it stands. The pick goes with the conversation
         that made it. */
      setAnswered(answeredIn(kept.at(-1)?.result ?? { scopes: [] }))
    })
    if (outcome === 'unreadable') setTrouble(UNDRAWABLE)
    if (outcome === 'drawn') {
      void parked(session.thread_id)
      void held(session.thread_id)
    }
  }

  /** Which field a reopened conversation is in. The pin outlived the page because it is
   *  the thread's own state; the picker is only where it is drawn. */
  const held = async (thread_id: string) => {
    /* A read that failed is no news about the field: `undefined` leaves the control as it
       stands, where `null` would re-open a picker on a thread the engine has closed and
       get the reader's next pick refused over a field they can no longer see. */
    const fixed = await cora.pinned(thread_id).catch(() => undefined)
    if (here.current !== thread_id || fixed === undefined) return
    setPin(fixed)
    setFixedPin(fixed !== null)
  }

  return (
    <div className="app">
      <div className="banners" role="status" aria-label="Notices">
        {banners.map(({ which, said }) => (
          <div key={which} className="trouble">
            {said}
          </div>
        ))}
      </div>

      <div className="columns">
        {/* The rail is always drawn, folded or not: the control that folds it lives in it,
            and a control that hides itself cannot be used to bring itself back. */}
        <aside className={leftOpen ? 'rail-docs' : 'rail-docs shut'}>
          <div className="rail-top">
            <span className="brand-name">cora</span>
            <RailToggle
              side="left"
              open={leftOpen}
              label="Documents"
              onToggle={() => setLeftOpen((shown) => !shown)}
            />
          </div>
          {leftOpen && (
            <>
              <NewSession canStart={somethingToLeave} onNew={start} />
              <DocumentRail
                documents={documents}
                cited={cited}
                field={field}
                onOpen={open}
                onUpload={uploaded}
                upload={notice}
                onDismissUpload={() => setNotice(null)}
              />
            </>
          )}
        </aside>

        <Answer
          mode={
            <ScopePicker
              available={fields}
              pin={pin}
              fixed={fixedPin}
              onPin={(scope) => setPin(scope === '' ? null : scope)}
            />
          }
          thread={thread}
          entries={conversation}
          asking={asking}
          askingElsewhere={working !== null && working !== thread}
          onAsk={ask}
          onCite={setOpened}
          onDecide={decided}
          onApprove={approve}
          onChange={change}
        />

        <aside className={rightOpen ? 'rail-panels' : 'rail-panels shut'}>
          <div className="rail-top">
            <RailToggle
              side="right"
              open={rightOpen}
              label="Plan & memory"
              onToggle={() => setRightOpen((shown) => !shown)}
            />
          </div>
          {rightOpen && (
          <>
          <div className="tabs" role="tablist">
            {TABS.map((name) => (
              <button
                key={name}
                role="tab"
                aria-selected={tab === name}
                className={tab === name ? 'tab active' : 'tab'}
                onClick={() => setTab(name)}
              >
                {name}
              </button>
            ))}
          </div>

          {tab === 'PLAN' && (
            <PlanPanel
              steps={live?.thread === thread ? live.steps : lastTrace(entries)}
            />
          )}
          {tab === 'SOURCE' && (
            <SourcePanel
              document={read?.document ?? null}
              source={read ? sourceOf(read) : null}
              citations={read ? passagesIn(read) : []}
            />
          )}
          {tab === 'SESSIONS' && (
            <SessionsPanel sessions={sessions} here={thread} onOpen={reopen} />
          )}
          {tab === 'MEMORY' && (
            <MemoryPanel
              facts={facts}
              onForget={(key) =>
                cora.forget(key).then(refresh).catch(reportTo(setTrouble))
              }
              onForgetEverything={() =>
                cora.forgetEverything().then(refresh).catch(reportTo(setTrouble))
              }
            />
          )}
          </>
          )}
        </aside>
      </div>

      {opened && <CitationModal citation={opened} onClose={() => setOpened(null)} />}
    </div>
  )
}

/** The turn the panels speak for: the newest one that actually answered. A turn that
 *  failed carries no citations and never will, so reading it as "this answer" takes the
 *  marks off the answer the reader is still reading. */
const answering = (entries: Entry[]): Entry | undefined =>
  entries.filter((entry) => !entry.error).at(-1)

/** The documents this conversation has actually rested on, by name. */
/** The one field a turn was answered in, or nothing where it named none or several —
 *  the rail draws one field, and a turn under two is not a turn it can follow. */
function answeredIn(reply: { scopes?: string[] }): string | null {
  return reply.scopes?.length === 1 ? reply.scopes[0] : null
}

/** The document an answer opens on: its first citation, in the field that citation was
 *  cut from. An answer that cited nothing leaves whatever was open. */
function _opened(reply: Result): { document: string; scope: string } | null {
  const [first] = reply.citations
  return first ? { document: first.document, scope: first.scope } : null
}

function citedDocuments(entries: Entry[], field: string): Set<string> {
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

function lastTrace(entries: Entry[]): Step[] {
  return entries.length ? entries[entries.length - 1].trace : []
}

/** What an upload did, in the words the page uses for what a document is made of. A store
 *  that already had those bytes indexes nothing and says so — the count is how the two
 *  outcomes differ, and it is the one thing the page used to throw away. */
const ingested = ({ document, chunks }: { document: string; chunks: number }): Notice =>
  chunks
    ? {
        said: `Added “${document}” — ${chunks} ${chunks === 1 ? 'passage' : 'passages'}.`,
        wrong: false,
      }
    : { said: `“${document}” is already in your documents.`, wrong: true }

const reportTo = (say: (said: string) => void) => (failed: unknown) =>
  say(message(failed))

const message = (failed: unknown) =>
  failed instanceof Error ? failed.message : String(failed)
