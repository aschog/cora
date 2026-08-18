import type { Doc } from '../data'
import DocumentBody from './DocumentBody'

const countLine = (doc: Doc) => {
  const n = doc.body.filter((p) => p.cited).length
  if (n === 0) return 'not cited in this answer'
  return n + (n === 1 ? ' cited passage' : ' cited passages') + ' · highlighted'
}

export default function SourcePanel({ doc }: { doc: Doc }) {
  return (
    <div>
      <div className="source-title">{doc.title}</div>
      <div className="source-meta">{doc.meta}</div>
      <div className="source-count">{countLine(doc)}</div>
      <DocumentBody doc={doc} />
      <div className="doc-note">{doc.note}</div>
    </div>
  )
}
