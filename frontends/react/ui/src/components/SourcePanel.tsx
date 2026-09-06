import type { Citation } from '../api'
import DocumentBody from './DocumentBody'
import { usePassage } from '../hooks/usePassage'
import styles from './SourcePanel.module.css'

type Props = {
  document: string | null
  /** Where the text is kept — the field and the upload. Any citation the conversation
   *  carries for this document names both, whether or not the newest answer rested on
   *  it. */
  source: { scope: string; upload: string } | null
  citations: Citation[]
}

export default function SourcePanel({ document, source, citations }: Props) {
  const { text, trouble } = usePassage(source)

  if (!document) return null

  return (
    <div>
      <h2 className={styles.sourceTitle}>{document}</h2>
      {citations.length === 0 && (
        <div className="micro">not cited in this answer</div>
      )}
      {trouble && <div className="trouble">{trouble}</div>}
      {text !== null && <DocumentBody text={text} spans={citations} />}
    </div>
  )
}
