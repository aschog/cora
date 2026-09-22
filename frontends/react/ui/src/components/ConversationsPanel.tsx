import type { ReactNode } from 'react'
import type { Conversation } from '../api'
import DeleteControl from './DeleteControl'
import styles from './ConversationsPanel.module.css'
import { joined } from '../joined'

const LEGEND =
  'A conversation with this mark is fixed to a field that has a page — open one and ' +
  'it opens as a chat in this rail, beside that page.'

const NEW = 'New conversation'

type Props = {
  conversations: Conversation[]
  here: string
  /** The conversation cora is answering a question in, if any. A turn that landed after
   *  its conversation was deleted would record it straight back into the list, so the
   *  one being answered in is left alone until it is done. */
  working: string | null
  onOpen: (conversation: Conversation) => void
  onDelete: (conversation: Conversation) => void
  /** Whether a conversation is one this rail would chat: fixed to a field that brings a
   *  page. The page and not the pin — a field pinned without one is drawn where every
   *  other conversation is. */
  chats: (conversation: Conversation) => boolean
  /** The conversation to be this panel, where the one the reader is in is chattable and
   *  they have not gone back to the list. The panel draws its head; what is passed is
   *  the conversation itself. */
  chat?: ReactNode
  /** What the conversation is about, for the head above it: the question that opened it. */
  about?: { opened: string }
  onBack?: () => void
}

export default function ConversationsPanel({
  conversations,
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
            aria-label="Back to other conversations"
            title="Back to other conversations"
            onClick={onBack}
          >
            ←
          </button>
          {/* The question it was opened with, which is what the list calls it too. What
              field it is in is the page beside it, and how long it is, is the scroll. */}
          <h3 className={styles.chatTitle} title={about.opened}>
            {about.opened || NEW}
          </h3>
        </div>
        {chat}
      </div>
    )
  }

  const marked = conversations.some(chats)
  return (
    <div className={styles.conversationList}>
      {conversations.map((conversation) => {
        /* A row in use offers no delete: the conversation on the page cannot be
           deleted, and neither can one still being answered in. */
        const inUse = conversation.thread_id === here || conversation.thread_id === working
        return (
          <div
            key={conversation.thread_id}
            className={joined(styles.conversationRow, conversation.thread_id === here && styles.here)}
          >
            {/* The mark is read out rather than drawn only, so what tells the rows apart
                is not a shape somebody has to have been told about. */}
            <span
              className={joined(styles.mark, chats(conversation) && styles.chatted)}
              aria-hidden={!chats(conversation)}
              aria-label={chats(conversation) ? `${conversation.opened_with} opens as a chat here` : undefined}
              role={chats(conversation) ? 'img' : undefined}
            />
            <button
              className={styles.conversation}
              /* The line is clamped so every row is one line high, and the whole
                 question is a hover away rather than lost. */
              title={conversation.opened_with}
              disabled={conversation.thread_id === here}
              onClick={() => onOpen(conversation)}
            >
              {conversation.opened_with}
            </button>
            {!inUse && (
              <DeleteControl
                what={conversation.opened_with}
                onDelete={() => onDelete(conversation)}
              />
            )}
          </div>
        )
      })}
      {marked && <p className={styles.legend}>{LEGEND}</p>}
    </div>
  )
}
