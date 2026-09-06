import styles from './UploadNotice.module.css'
import { joined } from '../joined'

/** What became of the last upload. An upload that indexed nothing is not trouble, but it is
 *  not the outcome the reader asked for either — `wrong` is what wears the alarm and the
 *  colour the page keeps for that, while a document actually added stays in the accent. */
export type Notice = { said: string; wrong: boolean }

export default function UploadNotice({
  said,
  wrong,
  onDismiss,
}: Notice & { onDismiss: () => void }) {
  return (
    <div className={joined(styles.uploadNotice, wrong && styles.wrong)}>
      {wrong && (
        <span className={styles.uploadNoticeMark} aria-hidden="true">
          !
        </span>
      )}
      <span className={styles.uploadNoticeSaid}>{said}</span>
      <button
        className={styles.uploadNoticeShut}
        aria-label="Dismiss"
        onClick={onDismiss}
      >
        ×
      </button>
    </div>
  )
}
