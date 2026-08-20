/** What became of the last upload. An upload that indexed nothing is not trouble, but it is
 *  not the outcome the reader asked for either — `wrong` is what wears the alarm and the
 *  colour the page keeps for that, while a document actually added stays in the accent. */
export type Notice = { said: string; wrong: boolean }

export default function UploadNotice({
  said,
  wrong,
  onDismiss,
}: Notice & { onDismiss: () => void }) {
  return (
    <div className={wrong ? 'upload-notice wrong' : 'upload-notice'}>
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
