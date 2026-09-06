import { useState } from 'react'
import type { Step } from '../api'
import styles from './PlanPanel.module.css'
import { joined } from '../joined'

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
    <div className={styles.plan}>
      {steps.map((step, n) => (
        <div key={n}>
          <button
            className={styles.planStep}
            aria-expanded={open === n}
            onClick={() => setOpen(open === n ? null : n)}
          >
            <span className={styles.planStepN}>{n + 1}</span>
            <span className={styles.planStepLabel}>{step.summary}</span>
            <span className={joined(styles.planStepMark, step.failed && styles.failed)}>
              {step.failed ? '✕' : '✓'}
            </span>
          </button>
          {open === n && (saysMore(step) || step.origin) && (
            <div className={styles.planDetail}>
              {saysMore(step) && <div className={styles.planResult}>{step.detail}</div>}
              {step.origin && (
                <div className={`micro ${styles.planOrigin}`}>{step.origin}</div>
              )}
            </div>
          )}
          {open === n && step.steps?.length > 0 && (
            <div
              className={styles.planInside}
              role="group"
              aria-label={`inside ${step.summary}`}
            >
              <PlanPanel steps={step.steps} />
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
