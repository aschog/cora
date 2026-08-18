import { useRef } from 'react'

type Props = {
  documents: string[]
  cited: Set<string>
  onOpen: (document: string) => void
  onUpload: (file: File) => void
}

const UNCITED =
  'Greyed documents are indexed but not cited in this conversation — ask something they can answer and they open here.'


export default function DocumentRail({ documents, cited, onOpen, onUpload }: Props) {
  const picker = useRef<HTMLInputElement>(null)

  return (
    <aside className="rail-docs">
      <div className="micro rail-heading">YOUR DOCUMENTS</div>

      <label className="upload">
        <span>＋</span>
        <span>Add a document</span>
        <input
          ref={picker}
          type="file"
          accept=".txt,.md,.pdf"
          onChange={(e) => {
            const [file] = Array.from(e.target.files ?? [])
            if (file) onUpload(file)
            e.target.value = ''
          }}
        />
      </label>

      {documents.length === 0 && (
        <div className="rail-empty">Nothing indexed yet.</div>
      )}

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

      {documents.some((name) => !cited.has(name)) && (
        <div className="rail-note">{UNCITED}</div>
      )}
    </aside>
  )
}
