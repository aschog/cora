import { useEffect } from 'react'
import type { Doc } from '../data'
import DocumentBody from './DocumentBody'

type Props = { doc: Doc; onClose: () => void }

export default function CitationModal({ doc, onClose }: Props) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <div className="overlay" onClick={onClose}>
      <div className="modal" role="dialog" aria-modal="true" aria-label={doc.title} onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <div>
            <div className="micro">CITED SOURCE</div>
            <div className="modal-title">{doc.title}</div>
            <div className="source-meta">{doc.meta}</div>
          </div>
          <button className="modal-close" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </div>
        <DocumentBody doc={doc} scrollToCited />
        <div className="doc-note">{doc.note}</div>
      </div>
    </div>
  )
}
