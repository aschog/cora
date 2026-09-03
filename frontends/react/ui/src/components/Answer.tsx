import { memo, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import type { MouseEvent } from 'react'
import { answerHtml } from '../answer'
import { patch } from '../patch'
import ApprovalCard from './ApprovalCard'
import DecisionCard from './DecisionCard'
import type { Citation } from '../api'
import { unanswered } from '../App'
import type { Entry } from '../App'

const WORKING = 'Working…'
const DECIDING = 'cora is waiting on your answer above.'
/** How close to the end still counts as reading the newest turn. A line of slack, so the
 *  fraction of a pixel a browser leaves behind at the bottom does not read as scrolling
 *  away. */
const NEAR_BOTTOM = 24
const ELSEWHERE =
  'cora is still answering a question in the conversation you left. It will be listed under SESSIONS when it lands.'

type Props = {
  /** Which conversation is on screen. Following is that conversation's — a reader
   *  halfway up one has said nothing about the next, which opens on its newest turn. */
  thread: string
  entries: Entry[]
  asking: boolean
  /** Asked in a conversation that is no longer on screen: cora answers one question at a
   *  time, so this page cannot be asked in either, and nothing on it would say why. */
  askingElsewhere: boolean
  onAsk: (question: string) => void
  onCite: (citation: Citation) => void
  onDecide: (entry: Entry, chosen: string | null) => void
  onApprove: (entry: Entry, call: string, approved: boolean) => void
  onChange: (entry: Entry) => void
}

export default function Answer({
  thread,
  entries,
  asking,
  askingElsewhere,
  onAsk,
  onCite,
  onDecide,
  onApprove,
  onChange,
}: Props) {
  const [question, setQuestion] = useState('')
  const scroller = useRef<HTMLDivElement>(null)
  /* Whether the conversation is still following what happens. An answer is written over
     half a minute and the effect below runs on every piece of it, so a reader who goes
     back to re-read an earlier turn has to be able to stay there. */
  const following = useRef(true)

  /* A turn asked, and a turn answered, both belong at the bottom of the scroller — the
     conversation follows what just happened rather than leaving it below the fold. All
     the way to the bottom, so the room the column leaves is what the last line clears
     the composer by. */
  useEffect(() => {
    following.current = true
  }, [thread])

  useEffect(() => {
    const shown = scroller.current
    if (shown && following.current) shown.scrollTop = shown.scrollHeight
  }, [entries.length, outcome(entries[entries.length - 1])])

  /* cora is parked on a question in this conversation, so there is one thing to do and
     it is not typing: two open questions on one thread would be two answers to one
     turn. */
  const parked = entries.some(unanswered)

  const send = () => {
    const asked = question.trim()
    if (!asked || asking || parked) return
    setQuestion('')
    /* Asking is the reader giving the conversation back: the question they just typed is
       the one thing that belongs on screen, wherever they had scrolled to. */
    following.current = true
    onAsk(asked)
  }

  return (
    <main className="answer">
      <div
        className="scroller"
        ref={scroller}
        onScroll={() => {
          const shown = scroller.current
          if (shown)
            following.current =
              shown.scrollHeight - shown.scrollTop - shown.clientHeight <= NEAR_BOTTOM
        }}
      >
        <div className="turn-column">
          {/* Keyed by the turn's own id. Ids repeat across conversations — every
              reopened thread numbers its turns from -1 — so React reconciles one
              conversation's second turn onto another's. Nothing rides on that while a
              turn holds no state of its own and `Written` memoises on the answer. */}
          {entries.map((entry) => (
            <div key={entry.id} className="turn">
              <p className="said">{entry.question}</p>
              <div className="from-cora">
                <span className="avatar" aria-hidden="true">
                  c
                </span>
                <span className="who">cora</span>
              </div>
              {entry.decision && (
                <DecisionCard
                  decision={entry.decision}
                  chosen={entry.chosen}
                  changing={!!entry.changing}
                  onChoose={(chosen) => onDecide(entry, chosen)}
                  onChange={() => onChange(entry)}
                />
              )}
              {/* One card per effect the turn proposed, in the order it proposed
                  them: a round may ask for two, and each is answered on its own. */}
              {(entry.proposals ?? []).map((each) => (
                <ApprovalCard
                  key={each.proposal.call_id}
                  proposal={each.proposal}
                  approved={each.approved}
                  onSettle={(approved) =>
                    onApprove(entry, each.proposal.call_id, approved)
                  }
                />
              ))}
              {/* What went wrong comes first, because it is the news whatever else the
                  turn has: a resume that failed leaves a card still waiting, and the
                  reader has to be told why before they answer it again. A turn in flight
                  with nothing written yet is the only one that says it is working — once
                  a word of it exists, that word is the news — and a turn waiting on the
                  reader says neither, because the card is what it has to say. */}
              {entry.error ? (
                <p className="trouble">{entry.error}</p>
              ) : unanswered(entry) ? null : entry.pending && !entry.answer ? (
                <p className="working">{WORKING}</p>
              ) : (
                <Written entry={entry} onCite={onCite} />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Outside the scroller, so it is always there to type in; the conversation
          passes behind it. */}
      <div className="composer-dock">
        <div className="composer">
          <input
            value={question}
            placeholder="Ask a question…"
            aria-label="Ask a question"
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && send()}
          />
          <button
            className="composer-ask"
            aria-label="Ask"
            onClick={send}
            disabled={asking || parked}
          >
            →
          </button>
        </div>
        {askingElsewhere && <p className="composer-note">{ELSEWHERE}</p>}
        {parked && <p className="composer-note">{DECIDING}</p>}
      </div>
    </main>
  )
}

/** One answer's rendered markdown, parsed when that answer changes and not when the
 *  composer's next keystroke re-renders the list around it, and *patched* into the block
 *  rather than assigned to it: an answer is written a piece at a time, and a reader who
 *  has selected a sentence of it keeps that selection only as long as the nodes it was
 *  made in are the nodes still on the page. */
const Written = memo(function Written({
  entry,
  onCite,
}: {
  entry: Entry
  onCite: (citation: Citation) => void
}) {
  const body = useRef<HTMLDivElement>(null)
  const html = useMemo(
    () => answerHtml(entry.answer ?? '', entry.citations),
    [entry.answer, entry.citations],
  )
  /* Before the browser paints, so the answer is never drawn a frame behind what the page
     knows — the piece that just arrived is the news. */
  useLayoutEffect(() => {
    if (body.current) patch(body.current, html)
  }, [html])
  return (
    <div
      className="answer-body"
      ref={body}
      onClick={(e) => opened(e, entry.citations, onCite)}
    />
  )
})

/** What a turn has become, so that a turn *replaced* in place — a failure landing where
 *  the answer would have been — is a change the scroller notices. Keying on the answer
 *  alone leaves a failure below the fold, reading as nothing having happened. */
const outcome = (entry?: Entry) =>
  entry &&
  (entry.answer ??
    entry.error ??
    (entry.decision || entry.proposals
      ? `${entry.chosen}/${(entry.proposals ?? [])
          .map((each) => each.approved)
          .join(',')}`
      : '…'))

/** The answer is rendered markdown, so its citations are buttons in that HTML rather
 *  than elements React placed — which makes the click one listener on the block. */
function opened(
  event: MouseEvent<HTMLDivElement>,
  citations: Citation[],
  onCite: (citation: Citation) => void,
): void {
  const clicked = (event.target as HTMLElement).closest('[data-cite]')
  if (!clicked) return
  /* An answer is written by the model over documents it read, so a link around a
     citation is a link the reader never chose. Opening the passage is the whole of what
     the click does. */
  event.preventDefault()
  const number = Number(clicked.getAttribute('data-cite'))
  const citation = citations.find((each) => each.number === number)
  if (citation) onCite(citation)
}
