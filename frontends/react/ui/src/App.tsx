import { useCallback, useEffect, useState } from 'react'
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
  question: string
  answer?: string
  error?: string
  citations: Citation[]
  trace: Step[]
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
  const [read, setRead] = useState<Citation | null>(null)
  const [opened, setOpened] = useState<Citation | null>(null)
  const [trouble, setTrouble] = useState<string | null>(null)
  const [leftOpen, setLeftOpen] = useState(true)
  const [rightOpen, setRightOpen] = useState(true)

  /** What the page shows beside the conversation, reloaded together: one banner for
   *  the three of them, and a load that goes through clears the last one's. */
  const refresh = useCallback(
    () =>
      Promise.all([cora.documents(), cora.memory(), cora.sessions()])
        .then(([indexed, kept, before]) => {
          setDocuments(indexed)
          setFacts(kept)
          setSessions(before)
          setTrouble(null)
        })
        .catch(reportTo(setTrouble)),
    [],
  )

  useEffect(() => {
    cora.plugins().then(setPlugins).catch(reportTo(setTrouble))
    refresh()
  }, [refresh])

  const cited = citedDocuments(entries)

  const ask = async (question: string) => {
    const taken: Step[] = []
    setLive(taken)
    setTab('PLAN')
    try {
      const result = await cora.ask(question, thread, (step) => {
        taken.push(step)
        setLive([...taken])
      })
      setEntries((said) => [...said, { question, ...result }])
      setRead(result.citations[0] ?? null)
    } catch (failed) {
      setEntries((said) => [
        ...said,
        { question, error: message(failed), citations: [], trace: taken },
      ])
    } finally {
      setLive(null)
      refresh()
    }
  }

  const open = (session: Session) => {
    cora
      .turns(session.thread_id)
      .then((kept) => {
        setThread(session.thread_id)
        setEntries(
          kept.map((turn) => ({ question: turn.question, ...turn.result })),
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
            onUpload={(file) =>
              cora.upload(file).then(refresh).catch(reportTo(setTrouble))
            }
          />
        )}

        <Answer entries={entries} asking={live !== null} onAsk={ask} onCite={setOpened} />

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
          {tab === 'SOURCE' && <SourcePanel citation={read} />}
          {tab === 'SESSIONS' && (
            <SessionsPanel sessions={sessions} here={thread} onOpen={open} />
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
