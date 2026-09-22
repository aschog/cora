import styles from './NewConversation.module.css'

type Props = { canStart: boolean; onNew: () => void }

const NOTHING_TO_START = 'You are already in a new conversation.'

/**
 * Reachable while it is unavailable, and carrying the reason: `disabled` would take the
 * control out of the accessibility tree, which is where the reason a page gives has to
 * be. `start` is what refuses — the rule has one writer.
 */
export default function NewConversation({ canStart, onNew }: Props) {
  return (
    <>
      <button
        className={styles.newConversation}
        aria-disabled={!canStart}
        aria-describedby={canStart ? undefined : 'new-conversation-why'}
        onClick={onNew}
      >
        <span className={styles.newConversationPlus} aria-hidden="true">
          +
        </span>
        New conversation
      </button>
      {!canStart && (
        <span id="new-conversation-why" className="told-not-shown">
          {NOTHING_TO_START}
        </span>
      )}
    </>
  )
}
