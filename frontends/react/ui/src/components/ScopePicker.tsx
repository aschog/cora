import { useEffect, useRef, useState } from 'react'

type Props = {
  /** The fields this deployment offers. None is a bare cora, and the picker is absent. */
  available: string[]
  /** The field this conversation is fixed to, or nothing while cora reads each question. */
  pin: string | null
  /** Whether the pin is settled in the thread's own state, which is what makes it final. */
  fixed: boolean
  onPin: (scope: string) => void
}

const CHAT = 'Chat'
const PICK = 'Plugin'
const ANSWER_IN = 'Answer in'
const TRIGGER = 'mode-plugin'
const LIST = 'mode-fields'
const ONE_WAY = 'A conversation keeps the field it is pinned to. Start a new one for another.'
const FROM_NEXT = 'From your next question on.'

/**
 * Which field the conversation is answered in. `Chat` is cora with every loaded plugin
 * available, reading each question and answering it in the field it belongs to; the
 * second segment names one plugin instead, and the conversation is that field's for good
 * — so the control is a one-way door and says so before it is used rather than after.
 *
 * Two segments whatever a deployment loaded, because the choice a reader makes is between
 * letting cora route and naming a field, not between eight fields. Which field is the
 * second question, and the menu answers it.
 *
 * `Chat` is a toggle and the second segment discloses a list, rather than both being
 * halves of one radio group: a control that is also a disclosure cannot be a radio, whose
 * whole claim is that it is one of a set of values with nothing behind it. The list is a
 * list of buttons and says no more than that — `menu` and `listbox` are composite widgets
 * whose arrow keys a reader is then entitled to, and buttons in a list need none.
 *
 * A pin picked here is not written anywhere yet: it lives in the thread's own state, and
 * only a turn writes there. `fixed` is what says a turn has.
 */
export default function ScopePicker({ available, pin, fixed, onPin }: Props) {
  const [open, setOpen] = useState(false)
  const wrap = useRef<HTMLDivElement>(null)
  const trigger = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (!open) return
    const away = (event: MouseEvent) => {
      if (wrap.current && !wrap.current.contains(event.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', away)
    return () => document.removeEventListener('mousedown', away)
  }, [open])

  /* The list stands over the conversation, so both ways out of it — abandoning it and
     using it — put the focus back where it came from. The button that was pressed is
     unmounted with the list it was in, and a reader who picked from the keyboard is left
     on nothing otherwise. Turning away is the exception: that reader is already elsewhere.
   */
  const shut = () => {
    setOpen(false)
    trigger.current?.focus()
  }

  const escape = (event: { key: string }) => {
    if (event.key === 'Escape') shut()
  }

  if (available.length === 0) return null

  /* Settled by a turn, there is nothing left to pick: the strip becomes the name it
     settled on. A control that can no longer be used is not drawn as one. */
  if (fixed && pin !== null)
    return (
      <div className="modes">
        <div className="mode-strip" role="group" aria-label={ANSWER_IN}>
          <span className="mode settled" aria-describedby="scope-why">
            {pin}
          </span>
        </div>
        <span id="scope-why" className="told-not-shown">
          {ONE_WAY}
        </span>
      </div>
    )

  return (
    <div className="modes">
      <div className="mode-strip" role="group" aria-label={ANSWER_IN}>
        <button
          className="mode"
          aria-pressed={pin === null}
          onClick={() => {
            setOpen(false)
            onPin('')
          }}
        >
          {CHAT}
        </button>
        <div className="mode-wrap" ref={wrap} onKeyDown={escape}>
          <button
            ref={trigger}
            id={TRIGGER}
            className="mode"
            aria-pressed={pin !== null}
            aria-expanded={open}
            aria-controls={LIST}
            onClick={() => setOpen((shown) => !shown)}
          >
            {pin ?? (
              <>
                <span className="mode-plus" aria-hidden="true">
                  +
                </span>
                {PICK}
              </>
            )}
          </button>
          {open && (
            <ul id={LIST} className="mode-menu">
              {available.map((scope) => (
                <li key={scope}>
                  <button
                    className="mode-option"
                    aria-current={pin === scope}
                    onClick={() => {
                      onPin(scope)
                      shut()
                    }}
                  >
                    {scope}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
      {pin !== null && <span className="scope-note">{FROM_NEXT}</span>}
    </div>
  )
}
