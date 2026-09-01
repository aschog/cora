import { useEffect } from 'react'
import type { Citation } from '../api'
import DocumentBody, { usePassage } from './DocumentBody'

type Props = { citation: Citation; onClose: () => void }

export default function CitationModal({ citation, onClose }: Props) {
  const { text, trouble } = usePassage(
    /* Both names, or neither: a citation stored before a passage carried its field
       names no field, and a request for one would leave the reader the router's 404
       rather than the sentence written for them. */
    citation.upload && citation.scope
      ? { scope: citation.scope, upload: citation.upload }
      : null,
  )

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <div className="overlay" onClick={onClose}>
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label={citation.document}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-head">
          <div>
            <div className="micro">CITED SOURCE</div>
            <div className="modal-title">{citation.document}</div>
          </div>
          <button className="modal-close" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </div>
        {trouble && <div className="trouble">{trouble}</div>}
        {text !== null && (
          <DocumentBody text={text} spans={[citation]} scrollToFirst />
        )}
      </div>
    </div>
  )
}
