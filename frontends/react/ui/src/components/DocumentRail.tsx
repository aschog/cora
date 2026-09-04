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
  /** The field an upload naming none lands in — a field like any other, so it is
   *  offered beside the loaded ones. The server says which it is. */
  anyField: string
  /** Whether the conversation's pin decides it. A pinned thread has one field for good,
   *  so the rail states it rather than offering it — and so does a deployment that
   *  loaded one field, where every turn runs in it and there is nothing to choose. */
  fixedField: boolean
  onField: (field: string) => void
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
  fields,
  field,
  anyField,
  fixedField,
  onField,
  onOpen,
  onUpload,
  upload,
  onDismissUpload,
}: Props) {
  /* The default field is offered beside the loaded ones because a turn belonging to
     none is answered in it. With one field loaded there is no such turn — routing has
     nothing to choose against — so it is not somewhere a document can usefully go. */
  const offered = [...fields.filter((each) => each !== anyField), anyField]
  const settled = fixedField || fields.length === 1

  return (
    <>
      <div className="micro rail-heading">YOUR DOCUMENTS</div>

      {fields.length > 0 && (
        <div className="upload-field">
          {/* A label points at a control, so where the field is settled there is none
              to point at: the name moves onto the value itself, which is then what a
              screen reader reads out. The same move the header's pin already makes. */}
          {settled ? (
            <span className="micro" id="upload-field-name">
              Upload into
            </span>
          ) : (
            <label className="micro" htmlFor="upload-field">
              Upload into
            </label>
          )}
          {settled ? (
            <span className="field-fixed" aria-labelledby="upload-field-name">
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
    </>
  )
}
