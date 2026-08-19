type Props = {
  said: string
  /** An upload that indexed nothing is not trouble, but it is not the outcome the reader
   *  asked for either — it wears the alarm and the colour the page keeps for that, while a
   *  document actually added stays in the accent. */
  wrong: boolean
  onDismiss: () => void
}

export default function UploadNotice({ said, wrong, onDismiss }: Props) {
  return (
    <div className={wrong ? 'upload-notice wrong' : 'upload-notice'} role="status">
      {wrong && (
        <span className="upload-notice-mark" aria-hidden="true">
          !
        </span>
      )}
      <span className="upload-notice-said">{said}</span>
      <button className="upload-notice-shut" aria-label="Dismiss" onClick={onDismiss}>
        ×
      </button>
    </div>
  )
}
