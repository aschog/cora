import type { Session } from '../api'

type Props = {
  sessions: Session[]
  here: string
  onOpen: (session: Session) => void
}

export default function SessionsPanel({ sessions, here, onOpen }: Props) {
  return (
    <div className="session-list">
      {sessions.map((session) => (
        <button
          key={session.thread_id}
          className="session"
          disabled={session.thread_id === here}
          onClick={() => onOpen(session)}
        >
          {session.opened_with}
        </button>
      ))}
    </div>
  )
}
