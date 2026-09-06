import styles from './NewSession.module.css'

type Props = { canStart: boolean; onNew: () => void }

const NOTHING_TO_START = 'You are already in a new session.'

/**
 * Reachable while it is unavailable, and carrying the reason: `disabled` would take the
 * control out of the accessibility tree, which is where the reason a page gives has to
 * be. `start` is what refuses — the rule has one writer.
 */
export default function NewSession({ canStart, onNew }: Props) {
  return (
    <>
      <button
        className={styles.newSession}
        aria-disabled={!canStart}
        aria-describedby={canStart ? undefined : 'new-session-why'}
        onClick={onNew}
      >
        <span className={styles.newSessionPlus} aria-hidden="true">
          +
        </span>
        New session
      </button>
      {!canStart && (
        <span id="new-session-why" className={styles.toldNotShown}>
          {NOTHING_TO_START}
        </span>
      )}
    </>
  )
}
