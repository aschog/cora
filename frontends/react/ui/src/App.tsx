import { useCallback, useEffect, useRef, useState } from 'react'
import * as cora from './api'
import type { Citation, Decision, Fact, Plugin, Session, Step, Turn } from './api'
import Answer from './components/Answer'
import CitationModal from './components/CitationModal'
import DocumentRail from './components/DocumentRail'
import Header from './components/Header'
import MemoryPanel from './components/MemoryPanel'
import PlanPanel from './components/PlanPanel'
import SessionsPanel from './components/SessionsPanel'
import SourcePanel from './components/SourcePanel'
import type { Notice } from './components/UploadNotice'

/** The field a question belonging to none is answered in, and where an upload naming no
 *  field lands. A field like any other, so the rail offers it beside the loaded ones. */
const ANY_FIELD = 'cora'

const TABS = ['STEPS', 'SOURCE', 'SESSIONS', 'MEMORY'] as const
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

const UNDRAWABLE = 'That conversation could not be read.'

/** One line the page says about itself, and which of them it is. */
type Banner = { which: string; said: string }

/** What became of a load: drawn on the page, dropped for a later one (or a store that
 *  could not be read, which says so itself), or read and undrawable. */
type Load = 'drawn' | 'dropped' | 'unreadable'

const newThread = () =>
  globalThis.crypto?.randomUUID?.() ?? String(Math.random()).slice(2)

export default function App() {
  const [tab, setTab] = useState<Tab>('STEPS')
  const [thread, setThread] = useState<string>(newThread)
  const [entries, setEntries] = useState<Entry[]>([])
  /* The turn being asked, and the conversation it is being asked in. Not one of
     `entries`: those are the turns the store has, and a reopen replaces them wholesale —
     which used to take the question the reader had just asked with it. */
  const [flight, setFlight] = useState<{ thread: string; entry: Entry } | null>(null)
  const [documents, setDocuments] = useState<string[]>([])
  const [plugins, setPlugins] = useState<Plugin[]>([])
  /* The fields this deployment offers, and the one this conversation is fixed to.
     `fixedPin` is whether a turn has written it into the thread's state — until one has,
     the pick is the reader's intention and the next question is what settles it. */
  const [fields, setFields] = useState<string[]>([])
  const [pin, setPin] = useState<string | null>(null)
  const [fixedPin, setFixedPin] = useState(false)
  /* The field the rail shows and uploads into. It follows the pin, because a pinned
     conversation has one field and a document put anywhere else could never be cited
     in it; unpinned, it is the reader's own pick and starts at the default field. */
  const [field, setField] = useState(ANY_FIELD)
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
  const [read, setRead] = useState<string | null>(null)
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
  const [rightOpen, setRightOpen] = useState(true)

  /** What the page shows around the conversation, loaded together: one banner for all
   *  of it, and a load that goes through clears the last one's. Loading the badge on
   *  its own raced that banner — a page that could not find out which plugin is loaded
   *  would say `bare cora` and then clear the only warning that it was guessing. */
  const refresh = useCallback(
    () =>
      Promise.all([
        cora.documents(field),
        cora.memory(),
        cora.sessions(),
        cora.plugins(),
        cora.scopes(),
      ])
        .then(([indexed, kept, before, loaded, offered]) => {
          setDocuments(indexed)
          setFacts(kept)
          setSessions(before)
          setPlugins(loaded)
          setFields(offered.available)
          setTrouble(null)
        })
        .catch(reportTo(setTrouble)),
    [field],
  )

  useEffect(() => {
    refresh()
  }, [refresh])

  /* A pinned conversation decides the rail's field: the pin is the thread's own state,
     so reopening one moves the rail with it. */
  useEffect(() => {
    if (pin !== null) setField(pin)
  }, [pin])

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

  const cited = citedDocuments(entries)
  /** What the conversation column shows: its recorded turns, and the one being asked in
   *  it. A turn in flight elsewhere is that conversation's, and is not drawn here. */
  const conversation =
    flight?.thread === thread ? [...entries, flight.entry] : entries

  /** The document as this conversation last had it. A filename names nothing on its
   *  own — one name can cover two uploads, and the store keeps a text per upload — so
   *  the newest citation for the name is what says which text to read. */
  const latestFor = (document: string) =>
    entries
      .slice()
      .reverse()
      .flatMap((entry) => entry.citations)
      .find((citation) => citation.document === document)

  /** Where a document's text is kept: the field it was ingested into and the upload it
   *  arrived as. Both, because a span is only meaningful against one field's file. */
  const sourceOf = (document: string) => {
    const found = latestFor(document)
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
  const passagesIn = (document: string) => {
    const upload = latestFor(document)?.upload
    return (answering(entries)?.citations ?? []).filter(
      (citation) => citation.document === document && citation.upload === upload,
    )
  }

  const open = (document: string) => {
    setRead(document)
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
        // reader, and what they pick lands on it where it stands.
        stow(on)
        if (here.current === on) {
          setEntries((said) => [
            ...said,
            {
              id,
              question,
              citations: [],
              trace: taken,
              decision: reply.decision,
            },
          ])
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
        setRead((current) => reply.citations[0]?.document ?? current)
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

  /** A decision answered. The turn is already on the page, so the rest of it lands on
   *  the entry that asked rather than after it. */
  const decide = async (entry: Entry, chosen: string | null) => {
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
      ...found,
      chosen,
      changing: false,
      pending: true,
      error: undefined,
    }))
    try {
      const reply = await cora.resume(
        on,
        chosen,
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
        at((found) => ({
          ...found,
          decision: reply.decision,
          chosen: undefined,
          pending: false,
        }))
        return
      }
      forget()
      at((found) => ({ ...found, ...reply, pending: false }))
      if (here.current === on)
        setRead((current) => reply.citations[0]?.document ?? current)
    } catch (failed) {
      /* Nothing was settled, so the card says nothing was: it goes back to waiting and
         the stow stays, which is what lets the reader pick again. */
      at((found) => ({
        ...found,
        chosen: undefined,
        error: message(failed),
        pending: false,
      }))
    } finally {
      setWorking(null)
      setLive(null)
      refresh()
    }
  }

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

  /** The question a conversation is still parked on, drawn after its turns: it is in no
   *  store, so nothing else on the page would bring it back. */
  const parked = async (thread_id: string) => {
    const waiting = await cora.pending(thread_id).catch(() => null)
    if (here.current !== thread_id) return
    /* A payload with no decision in it is not a pause, however it arrived: the card is
       drawn from the decision or not at all. */
    if (!waiting?.decision) {
      forgetIf(thread_id)
      return
    }
    stow(thread_id)
    setEntries((said) =>
      said.some((each) => each.decision && each.chosen === undefined)
        ? said
        : [
            ...said,
            {
              id: -(said.length + 1),
              question: waiting.asked,
              citations: [],
              trace: [],
              decision: waiting.decision,
            },
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
      <Header
        plugins={plugins}
        fields={fields}
        pin={pin}
        fixedPin={fixedPin}
        onPin={(scope) => setPin(scope === '' ? null : scope)}
        leftOpen={leftOpen}
        rightOpen={rightOpen}
        onToggleLeft={() => setLeftOpen((shown) => !shown)}
        onToggleRight={() => setRightOpen((shown) => !shown)}
        onNew={start}
        canStart={somethingToLeave}
      />

      <div className="banners" role="status" aria-label="Notices">
        {banners.map(({ which, said }) => (
          <div key={which} className="trouble">
            {said}
          </div>
        ))}
      </div>

      <div className="columns">
        {leftOpen && (
          <DocumentRail
            documents={documents}
            cited={cited}
            fields={fields}
            field={field}
            fixedField={pin !== null}
            onField={setField}
            onOpen={open}
            onUpload={uploaded}
            upload={notice}
            onDismissUpload={() => setNotice(null)}
          />
        )}

        <Answer
          thread={thread}
          entries={conversation}
          asking={asking}
          askingElsewhere={working !== null && working !== thread}
          onAsk={ask}
          onCite={setOpened}
          onDecide={decided}
          onChange={change}
        />

        {rightOpen && (
        <aside className="rail-panels">
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

          {tab === 'STEPS' && (
            <PlanPanel
              steps={live?.thread === thread ? live.steps : lastTrace(entries)}
            />
          )}
          {tab === 'SOURCE' && (
            <SourcePanel
              document={read}
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
        </aside>
        )}
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
function citedDocuments(entries: Entry[]): Set<string> {
  return new Set(
    entries.flatMap((entry) => entry.citations.map((citation) => citation.document)),
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
