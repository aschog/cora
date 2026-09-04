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
 * second question, and the list answers it.
 *
 * A pin picked here is not written anywhere yet: it lives in the thread's own state, and
 * only a turn writes there. `fixed` is what says a turn has.
 */
export default function ScopePicker({ available, pin, fixed, onPin }: Props) {
  const [open, setOpen] = useState(false)
  const wrap = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const away = (event: MouseEvent) => {
      if (wrap.current && !wrap.current.contains(event.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', away)
    return () => document.removeEventListener('mousedown', away)
  }, [open])

  if (available.length === 0) return null

  /* Settled by a turn, there is nothing left to pick: the strip becomes the name it
     settled on. A control that can no longer be used is not drawn as one — the same
     move the rail's `Upload into` makes. */
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
      <div className="mode-strip" role="radiogroup" aria-label={ANSWER_IN}>
        <button
          role="radio"
          className="mode"
          aria-checked={pin === null}
          onClick={() => {
            setOpen(false)
            onPin('')
          }}
        >
          {CHAT}
        </button>
        <div className="mode-wrap" ref={wrap}>
          <button
            role="radio"
            className="mode"
            aria-checked={pin !== null}
            aria-haspopup="listbox"
            aria-expanded={open}
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
            <ul className="mode-menu" role="listbox" aria-label={ANSWER_IN}>
              {available.map((scope) => (
                <li key={scope}>
                  <button
                    role="option"
                    className="mode-option"
                    aria-selected={pin === scope}
                    onClick={() => {
                      onPin(scope)
                      setOpen(false)
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
      <span className={pin === null ? 'told-not-shown' : 'scope-note'}>
        {pin === null ? '' : FROM_NEXT}
      </span>
    </div>
  )
}
