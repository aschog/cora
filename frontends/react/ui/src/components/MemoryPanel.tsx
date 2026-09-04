import type { Fact } from '../api'
import DeleteControl from './DeleteControl'

type Props = {
  facts: Fact[]
  /** The whole fact, not its key: what is about to go is put to the reader in its own
   *  words, and only the fact carries them. */
  onForget: (fact: Fact) => void
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
            <DeleteControl what={fact.text} onDelete={() => onForget(fact)} />
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
