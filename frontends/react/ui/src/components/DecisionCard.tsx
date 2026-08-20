import type { Decision } from '../api'

export const WAITING = 'Paused · needs your decision'
export const CHANGE = 'Change'
export const DECLINED = 'You chose none of them.'
export const chose = (label: string) => `You chose ${label}.`

type Props = {
  decision: Decision
  /** What the reader picked, once they have. `null` is choosing none of them, and absent
   *  is a card still waiting on them. */
  chosen?: string | null
  /** The card put back up: picking now corrects an answer rather than finishing one. */
  changing: boolean
  onChoose: (label: string | null) => void
  onChange: () => void
}

/** The question cora stopped on, and afterwards the line that says what it settled.
 *  One component over both because they are one thing in the conversation: the reader
 *  who answered it should find their answer where the question was. */
export default function DecisionCard({
  decision,
  chosen,
  changing,
  onChoose,
  onChange,
}: Props) {
  const open = chosen === undefined || changing
  return (
    <div className="decision" role="group" aria-label={WAITING}>
      <p className="decision-head micro">
        <span className="decision-dot" aria-hidden="true">
          ●
        </span>
        {WAITING}
      </p>
      {open ? (
        <>
          <p className="decision-question">{decision.question}</p>
          <div className="decision-options">
            {decision.options.map((option) => (
              <button
                key={option.label}
                className="decision-option"
                onClick={() => onChoose(option.label)}
              >
                <span className="decision-label">{option.label}</span>
                {option.note && <span className="decision-note">{option.note}</span>}
              </button>
            ))}
          </div>
          {decision.decline && (
            <button className="decision-decline" onClick={() => onChoose(null)}>
              {decision.decline}
            </button>
          )}
        </>
      ) : (
        <p className="decision-resolved">
          <span className="decision-settled">
            {chosen === null ? DECLINED : chose(chosen)}
          </span>
          <button className="decision-change" onClick={onChange}>
            {CHANGE}
          </button>
        </p>
      )}
    </div>
  )
}
