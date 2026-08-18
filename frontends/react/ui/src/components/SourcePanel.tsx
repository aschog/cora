import type { Citation } from '../api'
import DocumentBody, { usePassage } from './DocumentBody'

const NOTHING = 'A document you open, or the passage an answer cites, is shown here.'
const UNREADABLE = 'This document was indexed before cora kept its text, so it cannot be opened.'

type Props = {
  document: string | null
  /** Where the text is kept: any citation the conversation carries for this document
   *  names it, whether or not the newest answer rested on it. */
  upload: string | null
  citations: Citation[]
}

export default function SourcePanel({ document, upload, citations }: Props) {
  const { text, trouble } = usePassage(upload)

  if (!document) return <div className="panel-intro">{NOTHING}</div>

  return (
    <div>
      <div className="source-title">{document}</div>
      <div className="micro source-count">{counted(citations.length)}</div>
      {trouble && <div className="trouble">{trouble}</div>}
      {!upload && <div className="panel-intro">{UNREADABLE}</div>}
      {text !== null && <DocumentBody text={text} spans={citations} />}
    </div>
  )
}

const counted = (n: number) =>
  n === 0
    ? 'not cited in this answer'
    : `${n} cited ${n === 1 ? 'passage' : 'passages'} · highlighted`
