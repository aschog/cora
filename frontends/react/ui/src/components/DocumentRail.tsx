type Props = {
  documents: string[]
  cited: Set<string>
  onOpen: (document: string) => void
  onUpload: (file: File) => void
}

export default function DocumentRail({ documents, cited, onOpen, onUpload }: Props) {
  return (
    <aside className="rail-docs">
      <div className="micro rail-heading">YOUR DOCUMENTS</div>

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
