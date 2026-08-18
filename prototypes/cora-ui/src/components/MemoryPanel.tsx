import { MEMORY_FOOTER } from '../data'
import type { SavedLine } from '../data'

type Props = { saved: SavedLine[]; onDelete: (id: string) => void }

export default function MemoryPanel({ saved, onDelete }: Props) {
  return (
    <div>
      <div className="panel-intro">
        Only what you told cora to save. It never writes here on its own — say <em>remember that</em> and the line
        appears.
      </div>
      <div className="saved-list">
        {saved.map((line) => (
          <div key={line.id} className="saved-card">
            <div className="saved-head">
              <span className="saved-text">{line.text}</span>
              <button className="destructive" onClick={() => onDelete(line.id)}>
                delete
              </button>
            </div>
            <div className="micro saved-stamp">{line.stamp}</div>
          </div>
        ))}
      </div>
      <div className="panel-footer">{MEMORY_FOOTER}</div>
    </div>
  )
}
