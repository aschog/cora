import DeleteControl from './DeleteControl'
import UploadNotice from './UploadNotice'
import type { Notice } from './UploadNotice'
import styles from './DocumentRail.module.css'
import { joined } from '../joined'

type Props = {
  documents: string[]
  cited: Set<string>
  /** The field this rail lists and uploads into, or nothing where the strip above the
   *  conversation already names it. Stated, not offered, and only where saying it adds
   *  something: routing can settle a field nobody picked, and that is the one case
   *  where an upload would otherwise land somewhere unannounced. */
  field: string | null
  /** Every upload still running in this field, by the name it was uploaded as. Drawn as
   *  a row of its own: it is not a document of the field until the index holds it, so
   *  there is nothing to open and nothing to delete. */
  indexing: string[]
  /** The last upload that finished, or nothing. The list is what says an upload arrived
   *  to a reader who can see it; this is the same news for one who cannot, because a row
   *  *leaving* a live region is not announced. */
  indexed: string | null
  onOpen: (document: string) => void
  onUpload: (file: File) => void
  onDelete: (document: string) => void
  /** What the last upload did. It is drawn here rather than over the conversation: it is
   *  news about this list, raised by the control directly above it. */
  upload: Notice | null
  onDismissUpload: () => void
}

export default function DocumentRail({
  documents,
  cited,
  field,
  indexing,
  indexed,
  onOpen,
  onUpload,
  onDelete,
  upload,
  onDismissUpload,
}: Props) {
  return (
    <>
      {/* The heading names the list, and the field follows it in reading order. No ARIA
          between them: an association is what you reach for when the order cannot say it,
          and here it can — a `dl` would claim the heading is a term, and leave a `dt`
          with no `dd` in every state where no field is named. */}
      <div className={styles.railHeading}>
        <h2 className="micro">YOUR DOCUMENTS</h2>
        {field && <span className={styles.fieldFixed}>{field}</span>}
      </div>

      <label className={styles.upload}>
        <span>＋</span>
        <span>
          {indexing.length
            ? `Indexing ${indexing.length} file${indexing.length === 1 ? '' : 's'}…`
            : 'Add a document'}
        </span>
        {/* Named explicitly, because the label wraps the input and its text is
            therefore the input's own name: while anything is indexing that name would
            become the count, and a control has to say what taking it does. */}
        <input
          type="file"
          aria-label="Add a document"
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
        {indexed && (
          <p className={styles.toldNotShown}>{`“${indexed}” is indexed.`}</p>
        )}
        {upload && (
          <UploadNotice
            said={upload.said}
            wrong={upload.wrong}
            onDismiss={onDismissUpload}
          />
        )}
      </div>

      {/* Mounted whether or not anything is indexing, for the reason the region above it
          is: a live region a row arrives *into* is announced, one that arrives with its
          first row is not. */}
      <div className={styles.indexing} role="status" aria-label="Indexing">
        {indexing.map((name, at) => (
          /* Keyed by position: one name can be uploaded twice before either upload
             has answered, and these rows hold no state of their own to lose when a
             finished one shifts the rest along. */
          <div className={styles.indexingRow} key={at}>
            <span className={styles.indexingName}>{name}</span>
            <span className={styles.indexingState}>
              <span className={styles.indexingRing} aria-hidden="true" />
              <span className={joined('micro', styles.indexingWord)}>INDEXING</span>
              <span className={styles.indexingBar} aria-hidden="true" />
            </span>
          </div>
        ))}
      </div>

      <div className={styles.docList}>
        {documents.map((name) => (
          /* The control sits beside the row rather than inside it: the row is disabled
             unless this answer cited the document, and a delete nested in it would only
             reach the documents the last answer happened to quote. */
          <div key={name} className={styles.docLine}>
            <button
              className={joined(styles.docRow, cited.has(name) && styles.cited)}
              disabled={!cited.has(name)}
              onClick={() => onOpen(name)}
            >
              <span className={styles.docBar} />
              <span className={styles.docName}>{name}</span>
            </button>
            <DeleteControl what={name} onDelete={() => onDelete(name)} />
          </div>
        ))}
      </div>
    </>
  )
}
