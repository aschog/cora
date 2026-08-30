import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, test } from 'vitest'
import PlanPanel from './PlanPanel'
import type { Step } from '../api'

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

  const inside = container.querySelectorAll('.plan-inside .plan-step-label')
  expect([...inside].map((node) => node.textContent)).toEqual([
    'Decided to call search_documents',
    'search_documents(query="squats") → 1 passage',
  ])
})

test('a step that ran nothing of its own opens onto nothing', () => {
  const { container } = render(<PlanPanel steps={[step('Decided no tool was needed')]} />)

  fireEvent.click(screen.getByText('Decided no tool was needed'))

  expect(container.querySelector('.plan-inside')).toBeNull()
})

test('the steps are numbered as the turn took them', () => {
  const { container } = render(
    <PlanPanel steps={[step('first'), step('second')]} />,
  )

  const numbers = container.querySelectorAll('.plan-step-n')
  expect([...numbers].map((node) => node.textContent)).toEqual(['1', '2'])
})

test('a detail the line above already reads out is not drawn twice', () => {
  const call: Step = { ...step('add(a=1, b=2) → 3'), detail: '3' }

  const { container } = render(<PlanPanel steps={[call]} />)
  fireEvent.click(screen.getByText(call.summary))

  expect(container.querySelector('.plan-result')).toBeNull()
})

test('a detail that says more than the line above is drawn', () => {
  const call: Step = {
    ...step('search_documents(query="squats") → 1 passage from notes.md'),
    detail: '[1] notes.md: squats stall on sleep',
  }

  const { container } = render(<PlanPanel steps={[call]} />)
  fireEvent.click(screen.getByText(call.summary))

  expect(container.querySelector('.plan-result')?.textContent).toBe(
    '[1] notes.md: squats stall on sleep',
  )
})
