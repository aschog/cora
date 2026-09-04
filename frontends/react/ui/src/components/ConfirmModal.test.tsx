import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, test, vi } from 'vitest'
import ConfirmModal from './ConfirmModal'

const ASKED = {
  head: 'FORGET THIS',
  subject: 'No burpees.',
  said: 'cora stops using this in its answers.',
  confirm: 'Forget it',
}

afterEach(cleanup)

const asked = () => {
  const confirmed = vi.fn()
  const kept = vi.fn()
  render(<ConfirmModal {...ASKED} onConfirm={confirmed} onCancel={kept} />)
  return { confirmed, kept }
}

test('the question says what is going, what is lost, and what going ahead is called', () => {
  /* An icon says nothing about what is lost, and what is *kept* is the half a reader
     cannot see for themselves. The card is the only place they are told either. */
  asked()

  expect(screen.getByRole('dialog', { name: ASKED.head })).toBeTruthy()
  expect(screen.getByText(ASKED.subject)).toBeTruthy()
  expect(screen.getByText(ASKED.said)).toBeTruthy()
  expect(screen.getByRole('button', { name: ASKED.confirm })).toBeTruthy()
})

test('confirming answers the caller that raised the question', () => {
  const { confirmed, kept } = asked()

  fireEvent.click(screen.getByRole('button', { name: ASKED.confirm }))

  expect(confirmed).toHaveBeenCalled()
  expect(kept).not.toHaveBeenCalled()
})

test('keeping it answers the other way, and does nothing itself', () => {
  const { confirmed, kept } = asked()

  fireEvent.click(screen.getByRole('button', { name: 'Keep it' }))

  expect(kept).toHaveBeenCalled()
  expect(confirmed).not.toHaveBeenCalled()
})

test('escape and the page behind the card are both ways out', () => {
  /* The two the cited-source modal already answers to: a question with one answer is
     one a reader who changed their mind is stuck in. */
  const first = asked()
  fireEvent.keyDown(document, { key: 'Escape' })
  expect(first.kept).toHaveBeenCalled()
  expect(first.confirmed).not.toHaveBeenCalled()
  cleanup()

  const second = asked()
  fireEvent.click(screen.getByRole('dialog').parentElement!)
  expect(second.kept).toHaveBeenCalled()
  expect(second.confirmed).not.toHaveBeenCalled()
})
