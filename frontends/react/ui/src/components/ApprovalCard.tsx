import type { Proposal } from '../api'

export const WAITING = 'Paused · needs your approval'
export const SETTLED = 'Settled · your approval'
export const APPROVE = 'Approve'
export const DECLINE = 'Decline'
export const APPROVED = 'You approved it.'
export const DECLINED = 'You declined it. Nothing outside cora was changed.'

type Props = {
  proposal: Proposal
  /** What the reader answered, once they have. Absent is a card still waiting on them. */
  approved?: boolean
  onSettle: (approved: boolean) => void
}

/** What cora is about to do, and afterwards the line that says which way it went.
 *
 *  The settled line says what the reader did, not what came of it: the answer is written
 *  before the call runs, and a tool that then failed would leave a card claiming an
 *  effect that never happened. What came of it is the turn's answer to tell.
 *
 *  No way back onto the card, unlike a decision: a decision the reader answered one way
 *  can be asked again the other, and an effect that has happened cannot be taken back.
 *  Offering to change it would say otherwise. */
export default function ApprovalCard({ proposal, approved, onSettle }: Props) {
  const open = approved === undefined
  const state = open ? WAITING : SETTLED
  return (
    <div className="decision approval" role="group" aria-label={state}>
      <p className="decision-head micro">
        <span
          className={open ? 'decision-dot' : 'decision-dot settled'}
          aria-hidden="true"
        >
          ●
        </span>
        {state}
      </p>
      <p className="decision-question">{proposal.does}</p>
      {/* The call as it was really made: the tool's own name, and every argument the
          model wrote. Drawn whether the card is open or settled — a reader coming back
          to the conversation is owed what they approved, not only that they did. */}
      <dl className="approval-call">
        <div className="approval-tool">
          <dt>tool</dt>
          <dd>{proposal.tool}</dd>
        </div>
        {Object.entries(proposal.arguments).map(([name, value]) => (
          <div className="approval-argument" key={name}>
            <dt>{name}</dt>
            <dd>{written(value)}</dd>
          </div>
        ))}
      </dl>
      {open ? (
        <div className="approval-actions">
          <button className="approval-approve" onClick={() => onSettle(true)}>
            {APPROVE}
          </button>
          <button className="decision-decline" onClick={() => onSettle(false)}>
            {DECLINE}
          </button>
        </div>
      ) : (
        <p className="decision-resolved">
          <span className="decision-settled">{approved ? APPROVED : DECLINED}</span>
        </p>
      )}
    </div>
  )
}

/** An argument as the reader reads it. A string is what the model wrote and is shown as
 *  written; anything else is drawn as the JSON it arrived as, because a number, a list
 *  and a nested object all have to be readable and none of them is prose. */
const written = (value: unknown) =>
  typeof value === 'string' ? value : JSON.stringify(value)
