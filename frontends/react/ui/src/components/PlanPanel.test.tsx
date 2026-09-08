import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, test } from 'vitest'
import PlanPanel from './PlanPanel'
import type { Step } from '../api'
import planCss from '../components/PlanPanel.module.css'

const step = (summary: string, steps: Step[] = []): Step => ({
  summary,
  detail: '',
  failed: false,
  origin: '',
  steps,
})

afterEach(cleanup)

test('a step that ran work of its own shows that work under it', () => {
  const call = step('research(question="why?") → answered', [
    step('Decided to call search_documents'),
    step('search_documents(query="squats") → 1 passage'),
  ])

  const { container } = render(<PlanPanel steps={[call]} />)
  fireEvent.click(screen.getByText(call.summary))

  const inside = container.querySelectorAll(
    `.${planCss.planInside} .${planCss.planStepLabel}`,
  )
  expect([...inside].map((node) => node.textContent)).toEqual([
    'Decided to call search_documents',
    'search_documents(query="squats") → 1 passage',
  ])
})

test('a detail the line above already reads out is not drawn twice', () => {
  const call: Step = { ...step('add(a=1, b=2) → 3'), detail: '3' }

  const { container } = render(<PlanPanel steps={[call]} />)
  fireEvent.click(screen.getByText(call.summary))

  expect(container.querySelector(`.${planCss.planResult}`)).toBeNull()
})

