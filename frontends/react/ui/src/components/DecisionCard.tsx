import type { Decision } from '../api'

export const WAITING = 'Paused · needs your decision'
export const SETTLED = 'Settled · your decision'
export const CHANGE = 'Change'
/** A way out of every card, whether or not the model wrote one. The page has nothing
 *  else to offer while a card is open, so one with no control on it is a conversation
 *  the reader cannot leave. */
export const NO_OPTION = 'None of them'
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
  /* What the card is, said once: the head a reader sees and the name a screen reader
     hears are the same words, and a card that has been answered is not still paused. */
  const state = open ? WAITING : SETTLED
  return (
    <div className="decision" role="group" aria-label={state}>
      <p className="decision-head micro">
        <span
          className={open ? 'decision-dot' : 'decision-dot settled'}
          aria-hidden="true"
        >
          ●
        </span>
        {state}
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
          <button className="decision-decline" onClick={() => onChoose(null)}>
            {decision.decline || NO_OPTION}
          </button>
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
