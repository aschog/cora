import { PLAN_FOOTER, PLAN_STEPS } from '../data'

type Props = { open: Set<number>; onToggle: (n: number) => void }

export default function PlanPanel({ open, onToggle }: Props) {
  return (
    <div className="plan">
      {PLAN_STEPS.map((step) => (
        <div key={step.n}>
          <button className="plan-step" aria-expanded={open.has(step.n)} onClick={() => onToggle(step.n)}>
            <span className="plan-step-n">{step.n}</span>
            <span className="plan-step-label">{step.label}</span>
            <span className="plan-step-mark">✓</span>
          </button>
          {open.has(step.n) && (
            <div className="plan-detail">
              <div className="plan-call">{step.call}</div>
              <div className="plan-result">{step.result}</div>
              <div className="micro plan-origin">{step.origin}</div>
            </div>
          )}
        </div>
      ))}
      <div className="plan-footer">{PLAN_FOOTER}</div>
    </div>
  )
}
