import RailToggle from './RailToggle'
import ScopePicker from './ScopePicker'

type Props = {
  fields: string[]
  pin: string | null
  fixedPin: boolean
  onPin: (scope: string) => void
  leftOpen: boolean
  rightOpen: boolean
  onToggleLeft: () => void
  onToggleRight: () => void
  onNew: () => void
  canStart: boolean
}

const NOTHING_TO_START = 'You are already in a new session.'

export default function Header({
  fields,
  pin,
  fixedPin,
  onPin,
  leftOpen,
  rightOpen,
  onToggleLeft,
  onToggleRight,
  onNew,
  canStart,
}: Props) {
  return (
    <header className="header">
      <RailToggle side="left" open={leftOpen} label="Documents" onToggle={onToggleLeft} />

      <span className="brand-name">cora</span>

      <ScopePicker available={fields} pin={pin} fixed={fixedPin} onPin={onPin} />

      {/* Reachable while it is unavailable, and carrying the reason: `disabled` would
          take the control out of the accessibility tree, which is where the reason a page
          gives has to be. `start` is what refuses — the rule has one writer. */}
      <button
        className="new-session"
        aria-disabled={!canStart}
        aria-describedby={canStart ? undefined : 'new-session-why'}
        onClick={onNew}
      >
        <span className="new-session-plus" aria-hidden="true">
          +
        </span>
        New session
      </button>
      {!canStart && (
        <span id="new-session-why" className="told-not-shown">
          {NOTHING_TO_START}
        </span>
      )}

      <RailToggle
        side="right"
        open={rightOpen}
        label="Plan & memory"
        onToggle={onToggleRight}
      />
    </header>
  )
}
