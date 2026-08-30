import { useState } from 'react'
import type { Step } from '../api'

/** The trace as the panel draws it. A step that ran work of its own — a plugin's tool
 *  that delegated to the model — opens onto that work, drawn by this same panel one
 *  level in, so a reader sees what a call did rather than only that it was made. */
export default function PlanPanel({ steps }: { steps: Step[] }) {
  const [open, setOpen] = useState<number | null>(null)

  return (
    <div className="plan">
      {steps.map((step, n) => (
        <div key={n}>
          <button
            className="plan-step"
            aria-expanded={open === n}
            onClick={() => setOpen(open === n ? null : n)}
          >
            <span className="plan-step-n">{n + 1}</span>
            <span className="plan-step-label">{step.summary}</span>
            <span className={step.failed ? 'plan-step-mark failed' : 'plan-step-mark'}>
              {step.failed ? '✕' : '✓'}
            </span>
          </button>
          {open === n && (step.detail || step.origin) && (
            <div className="plan-detail">
              {step.detail && <div className="plan-result">{step.detail}</div>}
              {step.origin && <div className="micro plan-origin">{step.origin}</div>}
            </div>
          )}
          {open === n && step.steps?.length > 0 && (
            <div className="plan-inside">
              <PlanPanel steps={step.steps} />
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
