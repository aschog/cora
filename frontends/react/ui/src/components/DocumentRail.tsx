import UploadNotice from './UploadNotice'
import type { Notice } from './UploadNotice'

type Props = {
  documents: string[]
  cited: Set<string>
  /** The field this rail lists and uploads into, or nothing where the strip above the
   *  conversation already names it. Stated, not offered, and only where saying it adds
   *  something: routing can settle a field nobody picked, and that is the one case
   *  where an upload would otherwise land somewhere unannounced. */
  field: string | null
  onOpen: (document: string) => void
  onUpload: (file: File) => void
  /** What the last upload did. It is drawn here rather than over the conversation: it is
   *  news about this list, raised by the control directly above it. */
  upload: Notice | null
  onDismissUpload: () => void
}

export default function DocumentRail({
  documents,
  cited,
  field,
  onOpen,
  onUpload,
  upload,
  onDismissUpload,
}: Props) {
  return (
    <>
      {/* The heading names the list, and the field follows it in reading order. No ARIA
          between them: an association is what you reach for when the order cannot say it,
          and here it can — a `dl` would claim the heading is a term, and leave a `dt`
          with no `dd` in every state where no field is named. */}
      <div className="rail-heading">
        <h2 className="micro">YOUR DOCUMENTS</h2>
        {field && <span className="field-fixed">{field}</span>}
      </div>

      <label className="upload">
        <span>＋</span>
        <span>Add a document</span>
        <input
          type="file"
          accept=".txt,.md,.pdf"
          onChange={(e) => {
            const [file] = Array.from(e.target.files ?? [])
            if (file) onUpload(file)
            e.target.value = ''
          }}
        />
      </label>

      {/* Always drawn, so a sentence arriving in it is a change a screen reader announces.
          A region mounted together with its first content is not. Named because the page
          carries a second one for its own notices, and a name is what a reader hears before
          the sentence rather than after it. */}
      <div role="status" aria-label="Last upload">
        {upload && (
          <UploadNotice
            said={upload.said}
            wrong={upload.wrong}
            onDismiss={onDismissUpload}
          />
        )}
      </div>

      <div className="doc-list">
        {documents.map((name) => (
          <button
            key={name}
            className={cited.has(name) ? 'doc-row cited' : 'doc-row'}
            disabled={!cited.has(name)}
            onClick={() => onOpen(name)}
          >
            <span className="doc-bar" />
            <span className="doc-name">{name}</span>
          </button>
        ))}
      </div>
    </>
  )
}
