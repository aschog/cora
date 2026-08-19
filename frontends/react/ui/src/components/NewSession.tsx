type Props = { onStart: () => void }

export default function NewSession({ onStart }: Props) {
  return (
    <button className="new-session" onClick={onStart}>
      <span className="new-session-plus" aria-hidden="true">
        +
      </span>
      New session
    </button>
  )
}
