import type { Fact } from '../api'
import DeleteControl from './DeleteControl'

type Props = {
  facts: Fact[]
  onForget: (key: string) => void
  onForgetEverything: () => void
}

export default function MemoryPanel({
  facts,
  onForget,
  onForgetEverything,
}: Props) {
  return (
    <div>
      <div className="saved-list">
        {facts.map((fact) => (
          <div key={fact.key} className="saved-row">
            <span className="saved-text">{fact.text}</span>
            <DeleteControl what={fact.text} onDelete={() => onForget(fact.key)} />
          </div>
        ))}
      </div>
      {facts.length > 0 && (
        <button className="quiet forget-all" onClick={onForgetEverything}>
          forget everything
        </button>
      )}
    </div>
  )
}
