import type { Session } from '../api'

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
    <div className="session-list">
      {sessions.map((session) => (
        <div key={session.thread_id} className="session-row">
          <button
            className="session"
            disabled={session.thread_id === here}
            onClick={() => onOpen(session)}
          >
            {session.opened_with}
          </button>
          {session.thread_id !== here && session.thread_id !== working && (
            /* Named by the conversation it deletes: a row of buttons all reading
               "delete" says nothing about which one a reader is about to lose. */
            <button
              className="destructive"
              aria-label={`Delete ${session.opened_with}`}
              onClick={() => onDelete(session)}
            >
              delete
            </button>
          )}
        </div>
      ))}
    </div>
  )
}
