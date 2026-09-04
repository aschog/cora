import type { Fact } from '../api'

type Props = {
  facts: Fact[]
  onForget: (key: string) => void
  onForgetEverything: () => void
}

export default function MemoryPanel({ facts, onForget, onForgetEverything }: Props) {
  return (
    <div>
      <div className="saved-list">
        {facts.map((fact) => (
          <div key={fact.key} className="saved-card">
            <div className="saved-head">
              <span className="saved-text">{fact.text}</span>
              <button className="destructive" onClick={() => onForget(fact.key)}>
                forget
              </button>
            </div>
          </div>
        ))}
      </div>
      {facts.length > 0 && (
        <button className="destructive forget-all" onClick={onForgetEverything}>
          forget everything
        </button>
      )}
    </div>
  )
}
