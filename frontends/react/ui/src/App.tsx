import { useCallback, useEffect, useRef, useState } from 'react'
import * as cora from './api'
import type { Citation, Fact, Session, Step, Turn } from './api'
import Answer from './components/Answer'
import CitationModal from './components/CitationModal'
import DocumentRail from './components/DocumentRail'
import Header from './components/Header'
import MemoryPanel from './components/MemoryPanel'
import PlanPanel from './components/PlanPanel'
import SessionsPanel from './components/SessionsPanel'
import SourcePanel from './components/SourcePanel'

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
}

const UNDRAWABLE = 'That conversation could not be read.'

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
  const [plugins, setPlugins] = useState<string[]>([])
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
  const [asking, setAsking] = useState(false)
  const [read, setRead] = useState<string | null>(null)
  const [opened, setOpened] = useState<Citation | null>(null)
  const [trouble, setTrouble] = useState<string | null>(null)
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
        cora.documents(),
        cora.memory(),
        cora.sessions(),
        cora.plugins(),
      ])
        .then(([indexed, kept, before, loaded]) => {
          setDocuments(indexed)
          setFacts(kept)
          setSessions(before)
          setPlugins(loaded)
          setTrouble(null)
        })
        .catch(reportTo(setTrouble)),
    [],
  )

  useEffect(() => {
    refresh()
  }, [refresh])

  /** What the page has to say about itself, in one place: a load that failed, and a
   *  question left running that will not be answered. The second is not cleared by the
   *  next load going through, and says nothing once the reader is back in the
   *  conversation it belongs to — where the sentence would be false. */
  const banners = [
    ['load', trouble],
    ['lost', lost && lost.thread !== thread ? lost.said : null],
  ].filter((banner): banner is [string, string] => Boolean(banner[1]))

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

  const uploadOf = (document: string) => latestFor(document)?.upload ?? null

  /** Whether there is a conversation to leave: what the header draws, and what `start`
   *  refuses on. */
  const somethingToLeave = conversation.length > 0

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
    /* The answer as it is being written, and whether a step has arrived since the last
       piece of it. A step means the round that wrote this is over — a model may write an
       aside before calling a tool, and that aside is the trace's, kept as the step's own
       detail. So the next piece starts a new answer rather than continuing that one.
       Reset on the piece and not on the step, or the finished answer is blanked for the
       frame between the step that ends it and the turn that carries it. */
    let written = ''
    let superseded = false
    setAsking(true)
    setLost(null)
    setLive({ thread: on, steps: taken })
    setTab('PLAN')
    const id = ++asked.current
    setFlight({
      thread: on,
      entry: { id, question, citations: [], trace: [], pending: true },
    })
    try {
      const result = await cora.ask(
        question,
        thread,
        (step) => {
          taken.push(step)
          superseded = true
          setLive({ thread: on, steps: [...taken] })
        },
        (piece) => {
          if (superseded) {
            written = ''
            superseded = false
          }
          written += piece
          setFlight((running) =>
            running?.entry.id === id
              ? { ...running, entry: { ...running.entry, answer: written } }
              : running,
          )
        },
      )
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
          setEntries((said) => [...said, { id, question, ...result }])
        } else if ((await recall(on)) !== 'drawn' && here.current === on) {
          setEntries((said) => [...said, { id, question, ...result }])
        }
        setRead((current) => result.citations[0]?.document ?? current)
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
      setAsking(false)
      setLive(null)
      refresh()
    }
  }

  /** Starting over is a conversation the store is not asked for: it enters the same race
   *  as every load, so a reopen already in flight loses it rather than landing on top of
   *  the new session and taking the reader back. */
  const start = () => {
    if (!somethingToLeave) return
    const fresh = newThread()
    loads.current++
    here.current = fresh
    setThread(fresh)
    setEntries([])
    setRead(null)
    refresh()
  }

  const recall = (thread_id: string) =>
    loaded(thread_id, (kept) => setEntries(recorded(kept)))

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
    })
    if (outcome === 'unreadable') setTrouble(UNDRAWABLE)
  }

  return (
    <div className="app">
      <Header
        plugins={plugins}
        leftOpen={leftOpen}
        rightOpen={rightOpen}
        onToggleLeft={() => setLeftOpen((shown) => !shown)}
        onToggleRight={() => setRightOpen((shown) => !shown)}
        onNew={start}
        canStart={somethingToLeave}
      />

      <div className="banners" role="status">
        {banners.map(([which, said]) => (
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
            onOpen={open}
            onUpload={(file) =>
              cora.upload(file).then(refresh).catch(reportTo(setTrouble))
            }
          />
        )}

        <Answer
          entries={conversation}
          asking={asking}
          askingElsewhere={asking && flight?.thread !== thread}
          onAsk={ask}
          onCite={setOpened}
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

          {tab === 'PLAN' && (
            <PlanPanel
              steps={live?.thread === thread ? live.steps : lastTrace(entries)}
            />
          )}
          {tab === 'SOURCE' && (
            <SourcePanel
              document={read}
              upload={read ? uploadOf(read) : null}
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

const reportTo = (say: (said: string) => void) => (failed: unknown) =>
  say(message(failed))

const message = (failed: unknown) =>
  failed instanceof Error ? failed.message : String(failed)
