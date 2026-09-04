import { useState } from 'react'
import type { Session } from '../api'

type Props = {
  sessions: Session[]
  here: string
  /** The conversation cora is answering a question in, if any. A turn that landed after
   *  its conversation was deleted would record it straight back into the list, so the
   *  one being answered in is left alone until it is done. */
  working: string | null
  onOpen: (session: Session) => void
  onDelete: (session: Session) => void
}

const UNCOVERED = 56
/** How far a row is drawn before it is a gesture rather than a wobble. */
const A_GESTURE = 12

/** Where a row sits, and what is under the pointer while it is being drawn. `from` is
 *  where the gesture started; a row nothing is dragging has none. */
type Drawn = { thread: string; from: number | null; at: number }

export default function SessionsPanel({
  sessions,
  here,
  working,
  onOpen,
  onDelete,
}: Props) {
  const [drawn, setDrawn] = useState<Drawn | null>(null)

  const sitting = (thread: string) => (drawn?.thread === thread ? drawn.at : 0)

  /* Only one row is ever out: a rail of half-open rows says nothing about which
     conversation a delete belongs to. A gesture starts from where the row already sits,
     so a press that moves nowhere — the press on the uncovered control — leaves it
     where it was rather than reading as the drag undoing itself. */
  const start = (thread: string, from: number) =>
    setDrawn({ thread, from, at: sitting(thread) })

  const follow = (thread: string, to: number) =>
    setDrawn((held) =>
      held?.thread !== thread || held.from === null
        ? held
        : { ...held, at: Math.min(0, Math.max(-UNCOVERED, to - held.from)) },
    )

  /** Let go: the row snaps to uncovered or shut, whichever the gesture asked for — and
   *  a movement too small to be a gesture leaves it where it was. */
  const settle = (thread: string) =>
    setDrawn((held) =>
      held?.thread !== thread || held.from === null
        ? held
        : { thread, from: null, at: held.at <= -A_GESTURE ? -UNCOVERED : 0 },
    )

  return (
    <div className="session-list">
      {sessions.map((session) => {
        /* A row in use answers no gesture: the conversation on the page cannot be
           deleted, and neither can one still being answered in. */
        const inUse = session.thread_id === here || session.thread_id === working
        const at = inUse ? 0 : sitting(session.thread_id)
        return (
          <div key={session.thread_id} className="session-row">
            {/* The delete sits past the row's right edge, where the row's own overflow
                clips it, so what covers it is the width of the row rather than a colour
                painted over it. */}
            <div
              className="session-slide"
              style={{ transform: `translateX(${at}px)` }}
              onPointerDown={
                inUse ? undefined : (e) => start(session.thread_id, e.clientX)
              }
              onPointerMove={
                inUse ? undefined : (e) => follow(session.thread_id, e.clientX)
              }
              onPointerUp={inUse ? undefined : () => settle(session.thread_id)}
              onPointerCancel={inUse ? undefined : () => settle(session.thread_id)}
            >
              <button
                className="session"
                /* The line is clamped so every row is one line high, and the whole
                   question is a hover away rather than lost. */
                title={session.opened_with}
                disabled={session.thread_id === here}
                onClick={() => onOpen(session)}
              >
                {session.opened_with}
              </button>
              {!inUse && (
                /* Named by the conversation it deletes: a column of icons says nothing
                   about which one a reader is about to lose. Drawn whatever the row is
                   doing, so a keyboard reaches a delete no gesture can be made with. */
                <button
                  className="session-delete"
                  title={`Delete ${session.opened_with}`}
                  aria-label={`Delete ${session.opened_with}`}
                  onClick={() => onDelete(session)}
                >
                  <svg
                    width="15"
                    height="15"
                    viewBox="0 0 20 20"
                    fill="none"
                    aria-hidden="true"
                  >
                    <path
                      d="M3.5 5.5h13M8 5.5V3.8h4V5.5M5.2 5.5l.8 10.2a1.4 1.4 0 0 0 1.4 1.3h5.2a1.4 1.4 0 0 0 1.4-1.3l.8-10.2"
                      stroke="currentColor"
                      strokeWidth="1.4"
                      strokeLinecap="round"
                    />
                    <path
                      d="M8.4 8.4v5.6M11.6 8.4v5.6"
                      stroke="currentColor"
                      strokeWidth="1.4"
                      strokeLinecap="round"
                    />
                  </svg>
                </button>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
