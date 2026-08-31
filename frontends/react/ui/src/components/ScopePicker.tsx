type Props = {
  /** The fields this deployment offers. None is a bare cora, and the picker is absent. */
  available: string[]
  /** The field this conversation is fixed to, or nothing while cora reads each question. */
  pin: string | null
  /** Whether the pin is settled in the thread's own state, which is what makes it final. */
  fixed: boolean
  onPin: (scope: string) => void
}

const UNPINNED = 'cora reads each question'
const ONE_WAY = 'A conversation keeps the field it is pinned to. Start a new one for another.'
const FROM_NEXT = 'From your next question on.'

/**
 * Which field the conversation is in. Unpinned, cora reads every question and answers in
 * the field it belongs to; pinned, it is that field's for good — so the control is a
 * one-way door and says so before it is used rather than after.
 *
 * A pin picked here is not written anywhere yet: it lives in the thread's own state, and
 * only a turn writes there. `fixed` is what says a turn has.
 */
export default function ScopePicker({ available, pin, fixed, onPin }: Props) {
  if (available.length === 0) return null
  return (
    <div className="scope-wrap">
      {/* A label points at a control, so once the pin is fixed there is none to point
          at: the name moves onto the value itself, which is then what a screen reader
          reads out — an orphaned `for` would leave the field with no name at all. */}
      {fixed && pin !== null ? (
        <span className="scope-label" id="scope-field">
          Field
        </span>
      ) : (
        <label className="scope-label" htmlFor="scope-pin">
          Field
        </label>
      )}
      {fixed && pin !== null ? (
        <span
          className="scope-fixed"
          aria-labelledby="scope-field"
          aria-describedby="scope-why"
        >
          {pin}
        </span>
      ) : (
        <select
          id="scope-pin"
          className="scope-pick"
          value={pin ?? ''}
          onChange={(event) => onPin(event.target.value)}
        >
          <option value="">{UNPINNED}</option>
          {available.map((scope) => (
            <option key={scope} value={scope}>
              {scope}
            </option>
          ))}
        </select>
      )}
      <span id="scope-why" className={fixed ? 'told-not-shown' : 'scope-note'}>
        {fixed ? ONE_WAY : pin === null ? '' : FROM_NEXT}
      </span>
    </div>
  )
}
