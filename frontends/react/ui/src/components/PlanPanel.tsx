import { useState } from 'react'
import type { Step } from '../api'

const NOTHING = 'The steps cora takes will appear here.'
const FOOTER =
  'cora chose these steps. Nothing here is a fixed pipeline — the tools come from the loaded plugin.'

export default function PlanPanel({ steps }: { steps: Step[] }) {
  const [open, setOpen] = useState<number | null>(null)

  if (steps.length === 0) return <div className="panel-intro">{NOTHING}</div>

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
        </div>
      ))}
      <div className="plan-footer">{FOOTER}</div>
    </div>
  )
}
