import UploadNotice from './UploadNotice'
import type { Notice } from './UploadNotice'

type Props = {
  documents: string[]
  cited: Set<string>
  /** The fields this deployment loaded. Empty is a bare cora, which has one field and so
   *  nothing to choose between. */
  fields: string[]
  /** The field this rail is showing and uploading into. */
  field: string
  /** Whether the conversation's pin decides it. A pinned thread has one field for good,
   *  so the rail states it rather than offering it. */
  fixedField: boolean
  onField: (field: string) => void
  onOpen: (document: string) => void
  onUpload: (file: File) => void
  /** What the last upload did. It is drawn here rather than over the conversation: it is
   *  news about this list, raised by the control directly above it. */
  upload: Notice | null
  onDismissUpload: () => void
}

/** The default field, which is a field like any other and is always somewhere to put a
 *  document — it is what a bare cora answers in. */
const ANY = 'cora'

export default function DocumentRail({
  documents,
  cited,
  fields,
  field,
  fixedField,
  onField,
  onOpen,
  onUpload,
  upload,
  onDismissUpload,
}: Props) {
  const offered = [...fields.filter((each) => each !== ANY), ANY]

  return (
    <aside className="rail-docs">
      <div className="micro rail-heading">YOUR DOCUMENTS</div>

      {fields.length > 0 && (
        <div className="upload-field">
          <label className="micro" htmlFor="upload-field">
            Upload into
          </label>
          {fixedField ? (
            <span className="field-fixed" aria-label="Upload into">
              {field}
            </span>
          ) : (
            <select
              id="upload-field"
              value={field}
              onChange={(e) => onField(e.target.value)}
            >
              {offered.map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </select>
          )}
        </div>
      )}

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
    </aside>
  )
}
