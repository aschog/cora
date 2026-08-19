type Props = { onStart: () => void; can: boolean }

/** Nothing to start when the conversation is already an empty one on an unused thread. */
export default function NewSession({ onStart, can }: Props) {
  return (
    <button className="new-session" disabled={!can} onClick={onStart}>
      <span className="new-session-plus" aria-hidden="true">
        +
      </span>
      New session
    </button>
  )
}
