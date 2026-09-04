import UploadNotice from './UploadNotice'
import type { Notice } from './UploadNotice'

type Props = {
  documents: string[]
  cited: Set<string>
  /** The field this rail lists and uploads into. Stated, not offered: the strip above the
   *  conversation is what picks a field, and routing can settle one nobody picked — so
   *  the rail says where an upload lands rather than leaving it to be guessed. */
  field: string
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
      <div className="rail-heading">
        <span className="micro" id="rail-field">
          YOUR DOCUMENTS
        </span>
        <span className="field-fixed" aria-labelledby="rail-field">
          {field}
        </span>
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
