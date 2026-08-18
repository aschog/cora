import { memo, useEffect, useMemo, useRef, useState } from 'react'
import type { MouseEvent } from 'react'
import { answerHtml } from '../answer'
import type { Citation } from '../api'
import type { Entry } from '../App'

const WORKING = 'Working…'

type Props = {
  entries: Entry[]
  asking: boolean
  onAsk: (question: string) => void
  onCite: (citation: Citation) => void
}

export default function Answer({ entries, asking, onAsk, onCite }: Props) {
  const [question, setQuestion] = useState('')
  const scroller = useRef<HTMLDivElement>(null)

  /* A turn asked, and a turn answered, both belong at the bottom of the scroller — the
     conversation follows what just happened rather than leaving it below the fold. All
     the way to the bottom, so the room the column leaves is what the last line clears
     the composer by. */
  useEffect(() => {
    const shown = scroller.current
    if (shown) shown.scrollTop = shown.scrollHeight
  }, [entries.length, outcome(entries[entries.length - 1])])

  const send = () => {
    const asked = question.trim()
    if (!asked || asking) return
    setQuestion('')
    onAsk(asked)
  }

  return (
    <main className="answer">
      <div className="scroller" ref={scroller}>
        <div className="turn-column">
          {entries.map((entry, n) => (
            <div key={n} className="turn">
              <p className="said">{entry.question}</p>
              <div className="from-cora">
                <span className="avatar" aria-hidden="true">
                  c
                </span>
                <span className="who">cora</span>
              </div>
              {entry.pending ? (
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
