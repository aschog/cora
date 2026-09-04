import { useEffect } from 'react'

type Props = {
  /** The conversation being deleted, in the words it was opened with. */
  opened: string
  onConfirm: () => void
  onCancel: () => void
}

export const LOST =
  'The thread and its plan are removed. Your documents and saved memory are ' +
  "untouched — this can't be undone."

/** The question a delete is put to the reader as. A conversation cannot be asked for
 *  again once it is gone, which is what earns an overlay: forgetting a fact is a
 *  sentence you can say twice, and this is not. */
export default function DeleteModal({ opened, onConfirm, onCancel }: Props) {
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
        aria-label="Delete session"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="micro">DELETE SESSION</div>
        <div className="modal-title">{opened}</div>
        <p className="modal-said">{LOST}</p>
        <div className="modal-answers">
          <button className="quiet" onClick={onCancel}>
            Keep it
          </button>
          <button className="loud" onClick={onConfirm}>
            Delete session
          </button>
        </div>
      </div>
    </div>
  )
}
