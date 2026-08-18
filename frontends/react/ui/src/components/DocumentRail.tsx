import type { Doc } from '../data'

type Props = { docs: Doc[]; onPick: (key: string) => void; onUpload: (names: string[]) => void }

export default function DocumentRail({ docs, onPick, onUpload }: Props) {
  const cited = (doc: Doc) => doc.body.some((p) => p.cited)

  return (
    <aside className="rail-docs">
      <div className="micro rail-heading">YOUR DOCUMENTS</div>

      <label className="upload">
        <span>＋</span>
        <span>Add a document</span>
        <input
          type="file"
          multiple
          onChange={(e) => {
            const names = Array.from(e.target.files ?? []).map((f) => f.name)
            if (names.length) onUpload(names)
            e.target.value = ''
          }}
        />
      </label>

      <div className="doc-list">
        {docs.map((doc) => (
          <button
            key={doc.key}
            className={cited(doc) ? 'doc-row cited' : 'doc-row'}
            onClick={() => onPick(doc.key)}
          >
            <span className="doc-bar" />
            <span className="doc-name">{doc.name}</span>
          </button>
        ))}
      </div>
    </aside>
  )
}
