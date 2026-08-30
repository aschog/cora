import { useState } from 'react'
import type { Step } from '../api'

/** The trace as the panel draws it. A step that ran work of its own — a plugin's tool
 *  that delegated to the model — opens onto that work, drawn by this same panel to
 *  whatever depth the work went, so a reader sees what a call did rather than only that
 *  it was made. Children render only while their row is open, so depth costs clicks
 *  rather than render. */
/** Whether a step's detail says anything its own line does not. A call's line ends in
 *  what came back — `add(a=1, b=2) → 3` — so a detail of `3` under it is a row a reader
 *  opens for nothing, and one wasted row teaches them not to open the next. The
 *  recorder keeps the detail either way: a refusal is read there. */
function saysMore(step: Step): boolean {
  return step.detail !== '' && !step.summary.endsWith(`→ ${step.detail}`)
}

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
          {open === n && (saysMore(step) || step.origin) && (
            <div className="plan-detail">
              {saysMore(step) && <div className="plan-result">{step.detail}</div>}
              {step.origin && <div className="micro plan-origin">{step.origin}</div>}
            </div>
          )}
          {open === n && step.steps?.length > 0 && (
            <div className="plan-inside" role="group" aria-label={`inside ${step.summary}`}>
              <PlanPanel steps={step.steps} />
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
