import { memo, useEffect, useMemo, useRef, useState } from 'react'
import type { MouseEvent } from 'react'
import { answerHtml } from '../answer'
import type { Citation } from '../api'
import type { Entry } from '../App'

const WORKING = 'Working…'
/** How close to the end still counts as reading the newest turn. A line of slack, so the
 *  fraction of a pixel a browser leaves behind at the bottom does not read as scrolling
 *  away. */
const NEAR_BOTTOM = 24
const ELSEWHERE =
  'cora is still answering a question in the conversation you left. It will be listed under SESSIONS when it lands.'

type Props = {
  entries: Entry[]
  asking: boolean
  /** Asked in a conversation that is no longer on screen: cora answers one question at a
   *  time, so this page cannot be asked in either, and nothing on it would say why. */
  askingElsewhere: boolean
  onAsk: (question: string) => void
  onCite: (citation: Citation) => void
}

export default function Answer({
  entries,
  asking,
  askingElsewhere,
  onAsk,
  onCite,
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
    const shown = scroller.current
    if (shown && following.current) shown.scrollTop = shown.scrollHeight
  }, [entries.length, outcome(entries[entries.length - 1])])

  const send = () => {
    const asked = question.trim()
    if (!asked || asking) return
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
              {/* A turn in flight with nothing written yet is the only one that says
                  it is working: once a word of it exists, that word is the news. */}
              {entry.pending && !entry.answer ? (
                <p className="working">{WORKING}</p>
              ) : entry.error ? (
                <p className="trouble">{entry.error}</p>
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
            disabled={asking}
          >
            →
          </button>
        </div>
        {askingElsewhere && <p className="composer-note">{ELSEWHERE}</p>}
      </div>
    </main>
  )
}

/** One answer's rendered markdown, parsed when that answer changes and not when the
 *  composer's next keystroke re-renders the list around it. */
const Written = memo(function Written({
  entry,
  onCite,
}: {
  entry: Entry
  onCite: (citation: Citation) => void
}) {
  const html = useMemo(
    () => answerHtml(entry.answer ?? '', entry.citations),
    [entry.answer, entry.citations],
  )
  return (
    <div
      className="answer-body"
      onClick={(e) => opened(e, entry.citations, onCite)}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  )
})

/** What a turn has become, so that a turn *replaced* in place — a failure landing where
 *  the answer would have been — is a change the scroller notices. Keying on the answer
 *  alone leaves a failure below the fold, reading as nothing having happened. */
const outcome = (entry?: Entry) => entry && (entry.answer ?? entry.error ?? '…')

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
