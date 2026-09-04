import { useEffect } from 'react'

/** One question the page stops to have answered, in the words of whoever raised it. */
export type Asked = {
  /** What kind of question it is, over the subject: DELETE SESSION, FORGET THIS. */
  head: string
  /** What is about to go, in the words the reader knows it by. */
  subject: string
  /** What is lost, and what is not — the half a reader cannot see for themselves. */
  said: string
  /** What going ahead is called, so the button says what it does. */
  confirm: string
}

type Props = Asked & { onConfirm: () => void; onCancel: () => void }

/** The question either rail puts over the page before it takes something away. Told
 *  every word it says, so neither rail can put the other's wording on the page. */
export default function ConfirmModal({
  head,
  subject,
  said,
  confirm,
  onConfirm,
  onCancel,
}: Props) {
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onCancel()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onCancel])

  return (
    <div className="overlay" onClick={onCancel}>
      <div
        className="modal narrow"
        role="dialog"
        aria-modal="true"
        aria-label={head}
        onClick={(event) => event.stopPropagation()}
      >
        <div className="micro">{head}</div>
        <div className="modal-title">{subject}</div>
        <p className="modal-said">{said}</p>
        <div className="modal-answers">
          <button className="quiet" onClick={onCancel}>
            Keep it
          </button>
          <button className="loud" onClick={onConfirm}>
            {confirm}
          </button>
        </div>
      </div>
    </div>
  )
}
