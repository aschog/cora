import { SESSIONS_INTRO } from '../data'
import type { Inference } from '../data'

type Props = { inferences: Inference[]; onForget: (id: string) => void }

export default function SessionsPanel({ inferences, onForget }: Props) {
  return (
    <div>
      <div className="panel-intro">{SESSIONS_INTRO}</div>
      <div className="inference-list">
        {inferences.map((m) => (
          <div key={m.id} className="inference">
            <span className="inference-text">{m.text}</span>
            <button className="destructive" onClick={() => onForget(m.id)}>
              forget
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
