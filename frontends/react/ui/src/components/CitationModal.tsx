import { useEffect } from 'react'
import type { Citation } from '../api'
import DocumentBody from './DocumentBody'
import { usePassage } from '../hooks/usePassage'
import styles from './CitationModal.module.css'
import dialog from './dialog.module.css'

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
    <div className={dialog.overlay} onClick={onClose}>
      <div
        className={dialog.modal}
        role="dialog"
        aria-modal="true"
        aria-label={citation.document}
        onClick={(e) => e.stopPropagation()}
      >
        <div className={styles.modalHead}>
          <div>
            <div className="micro">CITED SOURCE</div>
            <div className={dialog.modalTitle}>{citation.document}</div>
          </div>
          <button className={styles.modalClose} onClick={onClose} aria-label="Close">
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
