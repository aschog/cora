import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, test, vi } from 'vitest'
import ApprovalCard, { APPROVE, APPROVED, DECLINE, DECLINED } from './ApprovalCard'

afterEach(cleanup)

const PROPOSAL = {
  call_id: 'c1',
  tool: 'save_itinerary',
  does: 'Save an itinerary as a Markdown file the user keeps.',
  arguments: { title: 'Kyoto, three days', days: 3 },
}

test('the card says what the call would do, and shows the call as it was made', () => {
  render(<ApprovalCard proposal={PROPOSAL} onSettle={() => {}} />)

  expect(screen.getByText(PROPOSAL.does)).toBeTruthy()
  expect(screen.getByText('save_itinerary')).toBeTruthy()
  expect(screen.getByText('Kyoto, three days')).toBeTruthy()
  expect(screen.getByText('3')).toBeTruthy()
})

test('approving and declining are both on the card, and each says which it was', () => {
  const settled = vi.fn()
  render(<ApprovalCard proposal={PROPOSAL} onSettle={settled} />)

  fireEvent.click(screen.getByRole('button', { name: APPROVE }))
  expect(settled).toHaveBeenCalledWith(true)

  fireEvent.click(screen.getByRole('button', { name: DECLINE }))
  expect(settled).toHaveBeenCalledWith(false)
})

test('an answered card reads as settled, saying which way it went', () => {
  const { rerender } = render(
    <ApprovalCard proposal={PROPOSAL} approved onSettle={() => {}} />,
  )

  expect(screen.getByText(APPROVED)).toBeTruthy()
  expect(screen.queryByRole('button', { name: APPROVE })).toBeNull()

  rerender(<ApprovalCard proposal={PROPOSAL} approved={false} onSettle={() => {}} />)
  expect(screen.getByText(DECLINED)).toBeTruthy()
})

test('a settled card still shows what was approved, not only that it was', () => {
  /* A reader coming back to the conversation is owed the call itself: "you approved it"
     over nothing is a record of a click rather than of what cora did. */
  render(<ApprovalCard proposal={PROPOSAL} approved onSettle={() => {}} />)

  expect(screen.getByText('Kyoto, three days')).toBeTruthy()
})
