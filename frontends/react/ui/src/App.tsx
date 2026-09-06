import { useEffect, useState } from 'react'
import * as cora from './api'
import type { Citation, Session } from './api'
import { answeredIn, lastTrace } from './entry'
import { reportTo } from './fail'
import { stowed } from './parked'
import { useConversation } from './hooks/useConversation'
import { useDocuments } from './hooks/useDocuments'
import { usePin } from './hooks/usePin'
import { useRails } from './hooks/useRails'
import { useSource } from './hooks/useSource'
import { useTurn } from './hooks/useTurn'
import Answer from './components/Answer'
import CitationModal from './components/CitationModal'
import ConfirmModal from './components/ConfirmModal'
import type { Asked } from './components/ConfirmModal'
import DocumentRail from './components/DocumentRail'
import NewSession from './components/NewSession'
import RailToggle from './components/RailToggle'
import ScopePicker from './components/ScopePicker'
import MemoryPanel from './components/MemoryPanel'
import PlanPanel from './components/PlanPanel'
import SessionsPanel from './components/SessionsPanel'
import SourcePanel from './components/SourcePanel'

const TABS = ['STEPS', 'SOURCE', 'SESSIONS', 'MEMORY'] as const
type Tab = (typeof TABS)[number]

const UNDRAWABLE = 'That conversation could not be read.'

/* What each question says is lost, and what is not — the half a reader cannot see for
   themselves. Written here, beside the rails that raise them. */
const DOCUMENT_GOES =
  'Its passages leave the index and its file leaves the field, so no answer can be ' +
  'drawn from it again. Answers already given keep their citations, and say the ' +
  "document is gone when you open one. This can't be undone."
const SESSION_GOES =
  'The thread and its plan are removed. Your documents and saved memory are ' +
  "untouched — this can't be undone."
const FACT_GOES =
  'cora stops using this in its answers. Your documents and your conversations are ' +
  "untouched — this can't be undone."
const EVERYTHING_GOES =
  'Every fact cora has been told is forgotten. Your documents and your conversations ' +
  "are untouched — this can't be undone."

/** One line the page says about itself, and which of them it is. */
type Banner = { which: string; said: string }

export default function App() {
  const [tab, setTab] = useState<Tab>('STEPS')
  const [trouble, setTrouble] = useState<string | null>(null)
  const [opened, setOpened] = useState<Citation | null>(null)
  /* What the page has stopped to have confirmed, and what to do once it is: the question
     stands over the page, and until it is answered nothing has been asked of cora. One
     slot, because one question stands at a time — and it carries the act, so each rail
     says its own words rather than the modal knowing everyone's. */
  const [confirming, setConfirming] = useState<
    (Asked & { act: () => Promise<void> }) | null
  >(null)
  const [leftOpen, setLeftOpen] = useState(true)
  const [rightOpen, setRightOpen] = useState(true)

  const {
    thread,
    entries,
    setEntries,
    here,
    loads,
    recall,
    start,
    reopen,
    parked,
    discard,
  } = useConversation(setTrouble)
  const { pin, fixedPin, answered, pick, held, reset, setAnswered } = usePin(here)
  const { documents, facts, sessions, fields, field, namedAbove, refresh } = useRails({
    pin,
    answered,
    setTrouble,
  })
  const { read, setRead, cited, sourceOf, passagesIn } = useSource(entries, field)
  const { notice, setNotice, upload, erase } = useDocuments({
    field,
    here,
    refresh,
    setTrouble,
    setRead,
  })
  const { flight, live, working, lost, ask, take, change } = useTurn({
    thread,
    here,
    loads,
    setEntries,
    recall,
    pin,
    held,
    setAnswered,
    setRead,
    setTab,
    refresh,
  })

  /** What the page shows around the conversation, and what else a conversation opened
   *  brings with it: the panel starts clean and the picker follows the turns that were
   *  actually answered. */
  const enterConversation = async (session: Session) => {
    const outcome = await reopen(session, (kept) => {
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

  /* A card left open outlives the page it was drawn on. The thread is already the one it
     was left in — `useConversation` opens there — so what is left is reading its turns
     and the question it stopped on back. Once, on the page being drawn. */
  useEffect(() => {
    /* Every write this makes is behind an `await` — the store is read first and nothing
       is set until it answers — which is the callback the rule asks for and cannot see
       through an async call. */
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (stowed()) void enterConversation({ thread_id: thread, opened_with: '' })
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

  /** What the conversation column shows: its recorded turns, and the one being asked in
   *  it. A turn in flight elsewhere is that conversation's, and is not drawn here. */
  const conversation = flight?.thread === thread ? [...entries, flight.entry] : entries

  /** Whether there is a conversation to leave: what the header draws, and what `start`
   *  refuses on. */
  const somethingToLeave = conversation.length > 0
  const asking = working !== null

  const open = (document: string) => {
    setRead({ document, scope: field })
    setTab('SOURCE')
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
              <NewSession
                canStart={somethingToLeave}
                onNew={() =>
                  start({
                    canLeave: somethingToLeave,
                    leaving: () => {
                      setRead(null)
                      setNotice(null)
                      reset()
                      refresh()
                    },
                  })
                }
              />
              <DocumentRail
                documents={documents}
                cited={cited}
                field={namedAbove ? null : field}
                onOpen={open}
                onUpload={upload}
                onDelete={(name) =>
                  setConfirming({
                    head: 'DELETE DOCUMENT',
                    subject: name,
                    said: DOCUMENT_GOES,
                    confirm: 'Delete document',
                    act: () => erase(field, name),
                  })
                }
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
              onPin={pick}
            />
          }
          thread={thread}
          entries={conversation}
          asking={asking}
          askingElsewhere={working !== null && working !== thread}
          onAsk={ask}
          onCite={setOpened}
          onTake={take}
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

              {tab === 'STEPS' && (
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
                <SessionsPanel
                  sessions={sessions}
                  here={thread}
                  working={working}
                  onOpen={enterConversation}
                  onDelete={(session) =>
                    setConfirming({
                      head: 'DELETE SESSION',
                      subject: session.opened_with,
                      said: SESSION_GOES,
                      confirm: 'Delete session',
                      act: () => discard(session),
                    })
                  }
                />
              )}
              {tab === 'MEMORY' && (
                <MemoryPanel
                  facts={facts}
                  onForget={(fact) =>
                    setConfirming({
                      head: 'FORGET THIS',
                      subject: fact.text,
                      said: FACT_GOES,
                      confirm: 'Forget it',
                      act: () => cora.forget(fact.key),
                    })
                  }
                  onForgetEverything={() =>
                    setConfirming({
                      head: 'FORGET EVERYTHING',
                      subject: 'Everything cora remembers about you',
                      said: EVERYTHING_GOES,
                      confirm: 'Forget everything',
                      act: () => cora.forgetEverything(),
                    })
                  }
                />
              )}
            </>
          )}
        </aside>
      </div>

      {opened && <CitationModal citation={opened} onClose={() => setOpened(null)} />}
      {confirming && (
        <ConfirmModal
          {...confirming}
          /* The question comes down as it is answered and the act runs after, so a
             banner the failure raises is not cleared by the card closing.
             The redraw and the refusal both belong here rather than in the act. The
             redraw, because a question may stand while a landing turn moves the field
             under it: this `refresh` asks about the field the rail is showing now,
             where the act's own would land the old field's listing under the new
             field's heading. The refusal, because nothing changed — a redraw would
             clear the sentence that says so. */
          onConfirm={() => {
            const going = confirming.act
            setConfirming(null)
            void going().then(refresh, reportTo(setTrouble))
          }}
          onCancel={() => setConfirming(null)}
        />
      )}
    </div>
  )
}
