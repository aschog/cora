import { useCallback, useEffect, useRef, useState } from 'react'
import * as cora from './api'
import type { Citation, Fact, Session, Step } from './api'
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

const newThread = () =>
  globalThis.crypto?.randomUUID?.() ?? String(Math.random()).slice(2)

export default function App() {
  const [tab, setTab] = useState<Tab>('PLAN')
  const [thread, setThread] = useState<string>(newThread)
  const [entries, setEntries] = useState<Entry[]>([])
  const [documents, setDocuments] = useState<string[]>([])
  const [plugins, setPlugins] = useState<string[]>([])
  const [facts, setFacts] = useState<Fact[]>([])
  const [sessions, setSessions] = useState<Session[]>([])
  const [live, setLive] = useState<Step[] | null>(null)
  /* Separate from `live`, which is a panel's contents: a conversation left behind drops
     the steps it was showing, while the request it left behind is still the one request
     cora is answering. One value cannot say both. */
  const [asking, setAsking] = useState(false)
  const [read, setRead] = useState<string | null>(null)
  const [opened, setOpened] = useState<Citation | null>(null)
  const [trouble, setTrouble] = useState<string | null>(null)
  const [leftOpen, setLeftOpen] = useState(true)
  const asked = useRef(0)
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

  const cited = citedDocuments(entries)

  /** Two different questions about one document, and answering both with the newest
   *  turn's citations was wrong. What is *marked* is what this answer rested on, or a
   *  document cited three turns ago accumulates marks until most of it is highlighted.
   *  What makes it *openable* is the upload its text is kept under, which any citation
   *  the conversation has ever carried for it names — a filename names nothing. */
  const passagesIn = (document: string) =>
    (entries[entries.length - 1]?.citations ?? []).filter(
      (citation) => citation.document === document,
    )

  const uploadOf = (document: string) =>
    entries
      .flatMap((entry) => entry.citations)
      .find((citation) => citation.document === document)?.upload ?? null

  const open = (document: string) => {
    setRead(document)
    setTab('SOURCE')
  }

  /** The question joins the thread the moment it is asked, so it is on the page while
   *  the answer is being written; what comes back replaces it rather than following
   *  it. */
  const ask = async (question: string) => {
    const on = thread
    const taken: Step[] = []
    setAsking(true)
    setLive(taken)
    setTab('PLAN')
    const id = ++asked.current
    setEntries((said) => [
      ...said,
      { id, question, citations: [], trace: [], pending: true },
    ])
    try {
      const result = await cora.ask(question, thread, (step) => {
        taken.push(step)
        // The plan is this conversation's; a reader who has moved on is not shown the
        // steps of a turn they left. The composer stays disabled until it ends either
        // way — cora answers one question at a time.
        if (here.current === on) setLive([...taken])
      })
      setEntries(answered({ id, question, ...result }))
      // The panels the answer steers are steered only if the reader is still in the
      // conversation it was asked in. An answer that cites nothing then leaves the
      // panel on the document last read, which says it is not cited in this answer —
      // rather than emptying the panel and saying nothing at all.
      if (here.current === on) {
        setRead((current) => result.citations[0]?.document ?? current)
      }
    } catch (failed) {
      setEntries(
        answered({
          id,
          question,
          error: message(failed),
          citations: [],
          trace: taken,
        }),
      )
    } finally {
      setAsking(false)
      if (here.current === on) setLive(null)
      refresh()
    }
  }

  const reopen = (session: Session) => {
    cora
      .turns(session.thread_id)
      .then((kept) => {
        here.current = session.thread_id
        setThread(session.thread_id)
        // Whatever a turn still in flight has drawn belongs to the conversation being
        // left, not to this one, which has its own last turn to show.
        setLive(null)
        setEntries(
          kept.map((turn, n) => ({
            id: -(n + 1),
            question: turn.question,
            ...turn.result,
          })),
        )
        setRead(null)
      })
      .catch(reportTo(setTrouble))
  }

  return (
    <div className="app">
      <Header
        plugins={plugins}
        leftOpen={leftOpen}
        rightOpen={rightOpen}
        onToggleLeft={() => setLeftOpen((shown) => !shown)}
        onToggleRight={() => setRightOpen((shown) => !shown)}
      />

      {trouble && <div className="trouble">{trouble}</div>}

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

        <Answer entries={entries} asking={asking} onAsk={ask} onCite={setOpened} />

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

          {tab === 'PLAN' && <PlanPanel steps={live ?? lastTrace(entries)} />}
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

/** The turn that was waiting, now that it is not — and nothing at all if the
 *  conversation it was asked in has since been left. */
const answered = (entry: Entry) => (said: Entry[]) =>
  said.map((each) => (each.id === entry.id ? entry : each))

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
