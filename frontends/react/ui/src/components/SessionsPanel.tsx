import type { Session } from '../api'
import DeleteControl from './DeleteControl'
import styles from './SessionsPanel.module.css'
import { joined } from '../joined'

type Props = {
  sessions: Session[]
  here: string
  /** The conversation cora is answering a question in, if any. A turn that landed after
   *  its conversation was deleted would record it straight back into the list, so the
   *  one being answered in is left alone until it is done. */
  working: string | null
  onOpen: (session: Session) => void
  onDelete: (session: Session) => void
}

export default function SessionsPanel({
  sessions,
  here,
  working,
  onOpen,
  onDelete,
}: Props) {
  return (
    <div className={styles.sessionList}>
      {sessions.map((session) => {
        /* A row in use offers no delete: the conversation on the page cannot be
           deleted, and neither can one still being answered in. */
        const inUse = session.thread_id === here || session.thread_id === working
        return (
          <div
            key={session.thread_id}
            className={joined(styles.sessionRow, session.thread_id === here && styles.here)}
          >
            <button
              className={styles.session}
              /* The line is clamped so every row is one line high, and the whole
                 question is a hover away rather than lost. */
              title={session.opened_with}
              disabled={session.thread_id === here}
              onClick={() => onOpen(session)}
            >
              {session.opened_with}
            </button>
            {!inUse && (
              <DeleteControl
                what={session.opened_with}
                onDelete={() => onDelete(session)}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}
