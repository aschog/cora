import { useEffect, useRef, useState } from 'react'
import DeleteControl from './DeleteControl'
import styles from './ScopePicker.module.css'

type Props = {
  /** The fields this deployment offers. Fewer than two is nothing to route between, and
   *  the picker is absent. */
  available: string[]
  /** The field this conversation is fixed to, or nothing while cora reads each question. */
  pin: string | null
  /** Whether the pin is settled in the thread's own state, which is what makes it final. */
  fixed: boolean
  /** Whether something else on the screen already names the field this conversation is
   *  in — the head over a conversation chatted beside its field's page does. Settled,
   *  this draws nothing then: a name that cannot be acted on, said twice, is one of them
   *  too many. The control itself is drawn either way, because picking is not naming. */
  namedElsewhere?: boolean
  /** The fields whose plugin this deployment can delete. A field the configuration
   *  named has none behind it, and one two plugins bring is not a question this control
   *  could answer — neither carries one. */
  deletable: string[]
  onPin: (scope: string) => void
  onDelete: (scope: string) => void
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
 * A field's plugin is deleted from the same list, from the control every rail carries —
 * the field is what a reader knows the plugin by, and it is what goes with it. The
 * question that follows is the page's, as it is for a document or a conversation:
 * nothing has been asked of cora when the control is used.
 *
 * A pin picked here is not written anywhere yet: it lives in the thread's own state, and
 * only a turn writes there. `fixed` is what says a turn has.
 */
export default function ScopePicker({
  available,
  pin,
  fixed,
  namedElsewhere = false,
  deletable,
  onPin,
  onDelete,
}: Props) {
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

  /* One field is not a choice: both segments answer in it, and naming it would fix the
     thread to it for good in exchange for nothing. None is a bare cora. Either way the
     rail is what says which field the documents are in.

     Unless there is a plugin to delete under it. The list is where a field's plugin is
     deleted from, and a deployment with one plugin is the whole of what dropping one in
     describes — leaving that one deletable by hand alone is the worse trade. Picking
     the field is still a pin, and still buys nothing, but it is now a choice the reader
     declines rather than one the page made for them. */
  if (available.length < 2 && deletable.length === 0) return null

  /* Settled by a turn, there is nothing left to pick: the strip becomes the name it
     settled on. A control that can no longer be used is not drawn as one — and why it
     cannot is written under the strip, where the promise it replaces was written. A
     description hung off a name nobody can focus is a description nobody is read. */
  if (fixed && pin !== null)
    return namedElsewhere ? null : (
      <div className={styles.modes}>
        <div className={styles.modeStrip} role="group" aria-label={ANSWER_IN}>
          <span className={`${styles.mode} ${styles.settled}`}>{pin}</span>
        </div>
        <span className={styles.scopeNote}>{ONE_WAY}</span>
      </div>
    )

  return (
    <div className={styles.modes}>
      <div className={styles.modeStrip} role="group" aria-label={ANSWER_IN}>
        <button
          className={styles.mode}
          aria-pressed={pin === null}
          onClick={() => {
            setOpen(false)
            onPin('')
          }}
        >
          {CHAT}
        </button>
        <div className={styles.modeWrap} ref={wrap} onKeyDown={escape}>
          <button
            ref={trigger}
            id={TRIGGER}
            className={styles.mode}
            aria-pressed={pin !== null}
            aria-expanded={open}
            aria-controls={LIST}
            onClick={() => setOpen((shown) => !shown)}
          >
            {pin ?? (
              <>
                <span className={styles.modePlus} aria-hidden="true">
                  +
                </span>
                {PICK}
              </>
            )}
          </button>
          {open && (
            <ul id={LIST} className={styles.modeMenu}>
              {available.map((scope) => (
                <li key={scope} className={styles.modeRow}>
                  <button
                    className={styles.modeOption}
                    aria-current={pin === scope}
                    onClick={() => {
                      onPin(scope)
                      shut()
                    }}
                  >
                    {scope}
                  </button>
                  {deletable.includes(scope) && (
                    <DeleteControl
                      what={`the ${scope} plugin`}
                      onDelete={() => {
                        shut()
                        onDelete(scope)
                      }}
                    />
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
      {pin !== null && <span className={styles.scopeNote}>{FROM_NEXT}</span>}
    </div>
  )
}
