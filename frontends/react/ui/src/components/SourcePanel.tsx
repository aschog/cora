import type { Citation } from '../api'
import DocumentBody, { usePassage } from './DocumentBody'

const NOTHING = 'The passage an answer cites will be shown here.'

export default function SourcePanel({ citation }: { citation: Citation | null }) {
  const { text, trouble } = usePassage(citation)

  if (!citation) return <div className="panel-intro">{NOTHING}</div>
  return (
    <div>
      <div className="source-title">{citation.document}</div>
      <div className="source-meta">
        cited as [{citation.number}] · characters {citation.start}–{citation.end}
      </div>
      {trouble && <div className="trouble">{trouble}</div>}
      {text !== null && <DocumentBody citation={citation} text={text} />}
    </div>
  )
}
