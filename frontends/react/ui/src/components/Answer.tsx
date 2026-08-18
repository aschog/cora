import { useState } from 'react'
import type { Citation } from '../api'
import type { Entry } from '../App'

const CITATION_RUN = /(?<![\w\]])(?:\[\d+\])+/g
/** What counts as a citation: the same rule the answer was written under — a run of
 *  brackets that continues neither a word nor another bracket. */

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
            <div className="micro">YOU ASKED</div>
            <p className="question">{entry.question}</p>
            {entry.error ? (
              <p className="trouble">{entry.error}</p>
            ) : (
              <div className="answer-body">{written(entry, onCite)}</div>
            )}
          </div>
        ))}

        {asking && <p className="working">{WORKING}</p>}

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

/** The answer as text and the citations in it as buttons; a number that resolves to no
 *  citation stays the text it was written as. */
function written(entry: Entry, onCite: (citation: Citation) => void) {
  const by = new Map(entry.citations.map((citation) => [citation.number, citation]))
  const pieces: (string | Citation)[] = []
  let read = 0
  for (const run of (entry.answer ?? '').matchAll(CITATION_RUN)) {
    pieces.push((entry.answer ?? '').slice(read, run.index))
    for (const number of run[0].matchAll(/\d+/g)) {
      const citation = by.get(Number(number[0]))
      pieces.push(citation ?? `[${number[0]}]`)
    }
    read = run.index + run[0].length
  }
  pieces.push((entry.answer ?? '').slice(read))

  return pieces.map((piece, n) =>
    typeof piece === 'string' ? (
      <span key={n}>{piece}</span>
    ) : (
      <button
        key={n}
        className="cite"
        aria-label={`Open cited source ${piece.number}`}
        onClick={() => onCite(piece)}
      >
        {piece.number}
      </button>
    ),
  )
}
