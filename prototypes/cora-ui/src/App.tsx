import { useMemo, useState } from 'react'
import { DOCS, INFERENCES, PLUGINS, SAVED_LINES, uploadedDoc } from './data'
import type { Doc } from './data'
import Header from './components/Header'
import DocumentRail from './components/DocumentRail'
import Answer from './components/Answer'
import PlanPanel from './components/PlanPanel'
import SourcePanel from './components/SourcePanel'
import SessionsPanel from './components/SessionsPanel'
import MemoryPanel from './components/MemoryPanel'
import CitationModal from './components/CitationModal'

const TABS = ['PLAN', 'SOURCE', 'SESSIONS', 'MEMORY'] as const
type Tab = (typeof TABS)[number]

export default function App() {
  const [tab, setTab] = useState<Tab>('PLAN')
  const [uploads, setUploads] = useState<Doc[]>([])
  const [sourceKey, setSourceKey] = useState('sleep')
  const [citedKey, setCitedKey] = useState<string | null>(null)
  const [openSteps, setOpenSteps] = useState(new Set([3]))
  const [plugin, setPlugin] = useState(PLUGINS[0].name)
  const [forgotten, setForgotten] = useState(new Set<string>())
  const [deleted, setDeleted] = useState(new Set<string>())

  const docs = useMemo(() => [...DOCS, ...uploads], [uploads])
  const byKey = (key: string) => docs.find((doc) => doc.key === key) ?? docs[0]

  const pickDoc = (key: string) => {
    setSourceKey(key)
    setTab('SOURCE')
    setCitedKey(null)
  }

  const toggleStep = (n: number) =>
    setOpenSteps((open) => {
      const next = new Set(open)
      if (!next.delete(n)) next.add(n)
      return next
    })

  const addToSet = <T,>(set: Set<T>, value: T) => new Set(set).add(value)

  return (
    <div className="app">
      <Header plugin={plugin} onPickPlugin={setPlugin} onOpenMemory={() => setTab('MEMORY')} />

      <div className="columns">
        <DocumentRail
          docs={docs}
          onPick={pickDoc}
          onUpload={(names) => setUploads((current) => [...current, ...names.map(uploadedDoc)])}
        />

        <Answer onCite={setCitedKey} />

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

          {tab === 'PLAN' && <PlanPanel open={openSteps} onToggle={toggleStep} />}
          {tab === 'SOURCE' && <SourcePanel doc={byKey(sourceKey)} />}
          {tab === 'SESSIONS' && (
            <SessionsPanel
              inferences={INFERENCES.filter((m) => !forgotten.has(m.id))}
              onForget={(id) => setForgotten((set) => addToSet(set, id))}
            />
          )}
          {tab === 'MEMORY' && (
            <MemoryPanel
              saved={SAVED_LINES.filter((line) => !deleted.has(line.id))}
              onDelete={(id) => setDeleted((set) => addToSet(set, id))}
            />
          )}
        </aside>
      </div>

      {citedKey && <CitationModal doc={byKey(citedKey)} onClose={() => setCitedKey(null)} />}
    </div>
  )
}
