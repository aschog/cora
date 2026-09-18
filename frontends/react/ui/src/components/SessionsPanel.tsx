import type { ReactNode } from 'react'
import type { Session } from '../api'
import DeleteControl from './DeleteControl'
import styles from './SessionsPanel.module.css'
import { joined } from '../joined'

const LEGEND =
  'A conversation with this mark is fixed to a field that has a page — open one and ' +
  'it opens as a chat in this rail, beside that page.'

const NEW = 'New conversation'

type Props = {
  sessions: Session[]
  here: string
  /** The conversation cora is answering a question in, if any. A turn that landed after
   *  its conversation was deleted would record it straight back into the list, so the
   *  one being answered in is left alone until it is done. */
  working: string | null
  onOpen: (session: Session) => void
  onDelete: (session: Session) => void
  /** Whether a conversation is one this rail would chat: fixed to a field that brings a
   *  page. The page and not the pin — a field pinned without one is drawn where every
   *  other conversation is. */
  chats: (session: Session) => boolean
  /** The conversation to be this panel, where the one the reader is in is chattable and
   *  they have not gone back to the list. The panel draws its head; what is passed is
   *  the conversation itself. */
  chat?: ReactNode
  /** What the conversation is about, for the head above it: the question that opened it,
   *  the field it is fixed to, and how many turns it holds. */
  about?: { opened: string; field: string; turns: number }
  onBack?: () => void
}

export default function SessionsPanel({
  sessions,
  here,
  working,
  onOpen,
  onDelete,
  chats,
  chat,
  about,
  onBack,
}: Props) {
  if (chat && about && onBack) {
    return (
      <div className={styles.chat}>
        <div className={styles.chatHead}>
          <button
            type="button"
            className={styles.back}
            aria-label="Back to other sessions"
            title="Back to other sessions"
            onClick={onBack}
          >
            ←
          </button>
          <div className={styles.chatNamed}>
            {/* The question it was opened with, which is what the list calls it too. */}
            <h3 className={styles.chatTitle} title={about.opened}>
              {about.opened || NEW}
            </h3>
            <p className={styles.chatMeta}>
              {about.field} · {about.turns} {about.turns === 1 ? 'message' : 'messages'}
            </p>
          </div>
        </div>
        {chat}
      </div>
    )
  }

  const marked = sessions.some(chats)
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
            {/* The mark is read out rather than drawn only, so what tells the rows apart
                is not a shape somebody has to have been told about. */}
            <span
              className={joined(styles.mark, chats(session) && styles.chatted)}
              aria-hidden={!chats(session)}
              aria-label={chats(session) ? `${session.opened_with} opens as a chat here` : undefined}
              role={chats(session) ? 'img' : undefined}
            />
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
      {marked && <p className={styles.legend}>{LEGEND}</p>}
    </div>
  )
}
