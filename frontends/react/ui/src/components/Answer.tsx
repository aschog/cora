import { useState } from 'react'
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

  const send = () => {
    const asked = question.trim()
    if (!asked || asking) return
    setQuestion('')
    onAsk(asked)
  }

  return (
    <main className="answer">
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
              <div
                className="answer-body"
                onClick={(e) => opened(e, entry.citations, onCite)}
                dangerouslySetInnerHTML={{
                  __html: answerHtml(entry.answer ?? '', entry.citations),
                }}
              />
            )}
          </div>
        ))}

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

/** The answer is rendered markdown, so its citations are buttons in that HTML rather
 *  than elements React placed — which makes the click one listener on the block. */
function opened(
  event: MouseEvent<HTMLDivElement>,
  citations: Citation[],
  onCite: (citation: Citation) => void,
): void {
  const clicked = (event.target as HTMLElement).closest('[data-cite]')
  if (!clicked) return
  const number = Number(clicked.getAttribute('data-cite'))
  const citation = citations.find((each) => each.number === number)
  if (citation) onCite(citation)
}
