import { useCallback, useEffect, useRef, useState } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import * as cora from './api'
import type { Citation, Fact, Scopes, Session } from './api'
import { answeredIn, lastTrace } from './entry'
import { stowed } from './parked'
import { showThread, threadInUrl } from './route'
import { useRoutedThread } from './hooks/useHash'
import { useConversation } from './hooks/useConversation'
import { useDocuments } from './hooks/useDocuments'
import { usePin } from './hooks/usePin'
import { rail, useRails } from './hooks/useRails'
import { useRemoving } from './hooks/useRemoving'
import type { Removal } from './hooks/useRemoving'
import { useSource } from './hooks/useSource'
import { useTurn } from './hooks/useTurn'
import Answer from './components/Answer'
import CitationModal from './components/CitationModal'
import ConfirmModal from './components/ConfirmModal'
import type { Asked } from './components/ConfirmModal'
import DocumentRail from './components/DocumentRail'
import ErrorBoundary from './components/ErrorBoundary'
import NewSession from './components/NewSession'
import RailToggle from './components/RailToggle'
import ScopePicker from './components/ScopePicker'
import MemoryPanel from './components/MemoryPanel'
import PlanPanel from './components/PlanPanel'
import SessionsPanel from './components/SessionsPanel'
import SourcePanel from './components/SourcePanel'
import styles from './App.module.css'
import { joined } from './joined'

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

/** What deleting a plugin takes, named field by field: it is the one control here that
 *  takes three things at once, so the question says all three. The fields are cora's
 *  answer — a field another plugin also brings is not one that goes, and a question
 *  naming it would overstate the loss on the most destructive control here. */
const pluginGoes = (fields: string[]) => {
  const one = fields.length === 1
  return (
    `Its files leave the plugins folder, and the ${one ? 'field' : 'fields'} ` +
    `${fields.join(' and ')} ${one ? 'goes' : 'go'} with them: every document ` +
    `${one ? 'it holds' : 'they hold'}, its passages, and every conversation pinned ` +
    'there. What cora remembers about you, and anything it saved for you, are ' +
    "untouched — this can't be undone."
  )
}

/** One line the page says about itself, and which of them it is. */
type Banner = { which: string; said: string }

/** What the rails are read through. `retry: false` because cora is one process on the
 *  other end of localhost: a read that failed did not lose a packet, and three silent
 *  attempts would only delay the sentence that says so. Refetching is what a turn, an
 *  upload or a delete asks for — not what the window regaining focus asks for, which
 *  would redraw the rails under a reader who was reading them.
 *
 *  Read rather than suspended on. `use()` and a Suspense boundary would draw a fallback
 *  per rail while it loads, and the page has one banner for all four on purpose: a
 *  boundary is where an error stops, so suspending the rails would put their failures in
 *  four places and leave the rule that they are told once with nowhere to live. */
const newStore = () =>
  new QueryClient({
    defaultOptions: { queries: { retry: false, refetchOnWindowFocus: false } },
  })

/** The page, and the store its rails are read out of. Two components because the store
 *  cannot be read by the one that provides it — and the provider is here rather than
 *  beside the root so that the page is one thing to draw, in a test as much as in a
 *  browser. */
export default function App() {
  const [store] = useState(newStore)
  return (
    <QueryClientProvider client={store}>
      <Page />
    </QueryClientProvider>
  )
}

function Page() {
  const [tab, setTab] = useState<Tab>('STEPS')
  /* What the page itself could not do, as opposed to what it could not read: an upload
     that was refused, a conversation that would not open, a delete that failed. The
     rails carry their own, and the banner below is both. */
  const [trouble, setTrouble] = useState<string | null>(null)
  const [opened, setOpened] = useState<Citation | null>(null)
  /* What the page has stopped to have confirmed, and what to do once it is: the question
     stands over the page, and until it is answered nothing has been asked of cora. One
     slot, because one question stands at a time — and it carries the act, so each rail
     says its own words rather than the modal knowing everyone's. */
  const [confirming, setConfirming] = useState<(Asked & Removal) | null>(null)
  const [leftOpen, setLeftOpen] = useState(true)
  const [rightOpen, setRightOpen] = useState(true)
  /* Which conversation the address names. Read from it rather than mirrored into state:
     the reader can change it, and two answers to "which conversation" can disagree. */
  const routed = useRoutedThread()

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
  const {
    documents,
    facts,
    sessions,
    plugins,
    fields,
    field,
    namedAbove,
    trouble: railTrouble,
    refresh: reread,
  } = useRails({ pin, answered })

  /** Everything the rails hold, read again — and what the page itself could not do let
   *  go of as it is. A reader asking for the listings again has moved past the upload
   *  that was refused, and the read that follows says for itself whether it went
   *  through. */
  const refresh = useCallback(async () => {
    setTrouble(null)
    await reread()
  }, [reread])
  /* Deleting is the one act the reader has already confirmed, so the row goes at the
     moment they say so — and comes back, with a sentence, if the store refuses. */
  const removing = useRemoving({ reread, setTrouble })
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
    /* A conversation the reader started becomes linkable the moment it has answered:
       until then it is in no store, and afterwards it is listed like any other. Replacing
       the entry rather than pushing one — they did not go anywhere, the page they are on
       acquired a name. */
    named: (thread_id) => showThread(thread_id, { replacing: true }),
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
      /* The address names the conversation that is drawn, and only once it is: a link to
         one that could not be read would otherwise sit in the bar describing a page the
         reader is not on. */
      showThread(session.thread_id)
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
    if (threadInUrl() || stowed()) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      void enterConversation({ thread_id: thread, opened_with: '' })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  /* The address changing *under* the page — the back button, a link pasted into the bar
     — is a request to be in another conversation. What the page itself just wrote is not:
     opening one writes the address, and following that back would load it twice.
     Compared against the last address this acted on rather than against the thread on the
     page, because the two disagree for every reason and only one of them is a
     navigation: a conversation the reader started, a load still in flight, a thread the
     store refused. Re-asserting the address over any of those takes them somewhere they
     did not ask to go. */
  const followed = useRef(routed)
  useEffect(() => {
    const asked = routed
    if (asked === followed.current) return
    followed.current = asked
    /* `here.current` rather than `thread`: `enter()` writes the ref synchronously while
       the state behind it is scheduled, so there is a window where this would see the new
       address against the old conversation and re-enter a load already running. */
    if (asked === null || asked === here.current) return
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void enterConversation({ thread_id: asked, opened_with: '' })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [routed])

  /** What the page has to say about itself, in one place: a load that failed, a question
   *  left running that will not be answered, and what became of the last upload. The
   *  second is not cleared by the next load going through, and says nothing once the
   *  reader is back in the conversation it belongs to — where the sentence would be false.
   *  What became of an upload is not here: it belongs beside the list it changed — which
   *  leaves both of these trouble, so the strip has one look rather than a tone each. */
  const banners = [
    /* What the page could not do outranks what it could not read: the reader just tried
       something, and that answer is the one they are waiting for. */
    { which: 'load', said: trouble ?? railTrouble },
    { which: 'lost', said: lost && lost.thread !== thread ? lost.said : null },
  ].filter((banner): banner is Banner => Boolean(banner.said))

  /** What the conversation column shows: its recorded turns, and the one being asked in
   *  it. A turn in flight elsewhere is that conversation's, and is not drawn here. */
  const conversation = flight?.thread === thread ? [...entries, flight.entry] : entries

  /** Whether there is a conversation to leave: what the header draws, and what `start`
   *  refuses on. */
  const somethingToLeave = conversation.length > 0
  const asking = working !== null

  /** The plugin a field carries a delete control for, or nothing. Exactly one loaded
   *  plugin, and one this deployment can delete: a field the configuration named has no
   *  plugin behind it, and a field two plugins bring is not a question one control could
   *  answer — which of them the reader meant, and what would be left holding the field. */
  const behind = (scope: string) => {
    const bringing = plugins.filter((each) => each.scopes.includes(scope))
    return bringing.length === 1 && bringing[0].deletable ? bringing[0] : null
  }

  const open = (document: string) => {
    setRead({ document, scope: field })
    setTab('SOURCE')
  }

  return (
    <div className={styles.app}>
      <div className={styles.banners} role="status" aria-label="Notices">
        {banners.map(({ which, said }) => (
          <div key={which} className="trouble">
            {said}
          </div>
        ))}
      </div>

      <div className={styles.columns}>
        {/* The rail is always drawn, folded or not: the control that folds it lives in it,
            and a control that hides itself cannot be used to bring itself back. */}
        <aside className={joined(styles.railDocs, !leftOpen && styles.shut)}>
          <div className={styles.railTop}>
            <span className={styles.brandName}>cora</span>
            <RailToggle
              side="left"
              open={leftOpen}
              label="Documents"
              onToggle={() => setLeftOpen((shown) => !shown)}
            />
          </div>
          {leftOpen && (
            <ErrorBoundary said="The documents rail could not be drawn.">
              <NewSession
                canStart={somethingToLeave}
                onNew={() =>
                  start({
                    canLeave: somethingToLeave,
                    leaving: () => {
                      /* A fresh thread is in no store and has nothing to link to, so the
                         address goes back to naming no conversation at all. */
                      showThread(null)
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
                    send: () => erase(field, name),
                    from: rail.documents(field),
                    without: (listed: string[]) =>
                      listed.filter((each) => each !== name),
                  })
                }
                upload={notice}
                onDismissUpload={() => setNotice(null)}
              />
            </ErrorBoundary>
          )}
        </aside>

        {/* Each column catches its own, so a rail that cannot be drawn costs the reader
            that rail rather than the conversation they were reading. */}
        <ErrorBoundary said="This conversation could not be drawn.">
          <Answer
            mode={
              <ScopePicker
                available={fields}
                pin={pin}
                fixed={fixedPin}
                deletable={fields.filter((scope) => behind(scope) !== null)}
                onPin={pick}
                onDelete={(scope) => {
                  const plugin = behind(scope)
                  if (plugin === null) return
                  setConfirming({
                    head: 'DELETE PLUGIN',
                    subject: plugin.name,
                    said: pluginGoes(plugin.going),
                    confirm: 'Delete plugin',
                    send: () => cora.deletePlugin(plugin.name),
                    from: rail.scopes,
                    /* The fields go with the plugin, so the picker loses them at the
                       moment the reader says so — the same act as a row leaving a rail,
                       over the listing the picker is drawn from. */
                    without: (held: Scopes) => ({
                      ...held,
                      available: held.available.filter(
                        (each) => !plugin.going.includes(each),
                      ),
                    }),
                  })
                }}
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
        </ErrorBoundary>

        <aside className={joined(styles.railPanels, !rightOpen && styles.shut)}>
          <div className={styles.railTop}>
            <RailToggle
              side="right"
              open={rightOpen}
              label="Plan & memory"
              onToggle={() => setRightOpen((shown) => !shown)}
            />
          </div>
          {rightOpen && (
            <>
              <div className={styles.tabs} role="tablist">
                {TABS.map((name) => (
                  <button
                    key={name}
                    role="tab"
                    aria-selected={tab === name}
                    className={joined(styles.tab, tab === name && styles.active)}
                    onClick={() => setTab(name)}
                  >
                    {name}
                  </button>
                ))}
              </div>

              {/* Keyed on the tab, so a panel that could not be drawn is left behind by
                  moving to another one — the strip above stays outside this for the same
                  reason, as the way out of a panel that broke. */}
              <ErrorBoundary key={tab} said="This panel could not be drawn.">
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
                        send: () => discard(session),
                        from: rail.sessions,
                        without: (listed: Session[]) =>
                          listed.filter((each) => each.thread_id !== session.thread_id),
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
                        send: () => cora.forget(fact.key),
                        from: rail.memory,
                        without: (listed: Fact[]) =>
                          listed.filter((each) => each.key !== fact.key),
                      })
                    }
                    onForgetEverything={() =>
                      setConfirming({
                        head: 'FORGET EVERYTHING',
                        subject: 'Everything cora remembers about you',
                        said: EVERYTHING_GOES,
                        confirm: 'Forget everything',
                        send: () => cora.forgetEverything(),
                        from: rail.memory,
                        without: () => [],
                      })
                    }
                  />
                )}
              </ErrorBoundary>
            </>
          )}
        </aside>
      </div>

      {opened && <CitationModal citation={opened} onClose={() => setOpened(null)} />}
      {confirming && (
        <ConfirmModal
          {...confirming}
          /* The question comes down as it is answered and the row goes with it; what
             the store says about it lands after. Neither the redraw nor the sentence is
             written here any more — `useRemoving` owns both, because the rollback and
             the sentence that explains it have to be the same step. */
          onConfirm={() => {
            const going = confirming
            setConfirming(null)
            removing.mutate(going)
          }}
          onCancel={() => setConfirming(null)}
        />
      )}
    </div>
  )
}
