import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, test, vi } from 'vitest'
import DeleteModal, { LOST } from './DeleteModal'

const OPENED = 'A question asked twice'

afterEach(cleanup)

const asked = () => {
  const confirmed = vi.fn()
  const kept = vi.fn()
  render(<DeleteModal opened={OPENED} onConfirm={confirmed} onCancel={kept} />)
  return { confirmed, kept }
}

test('the question names the conversation and what deleting it takes with it', () => {
  /* A row of icons says nothing about what is lost, and a conversation is more than
     the turns the reader can see. The card is the only place they are told. */
  asked()

  expect(screen.getByRole('dialog')).toBeTruthy()
  expect(screen.getByText(OPENED)).toBeTruthy()
  expect(screen.getByText(LOST)).toBeTruthy()
})

test('confirming asks for the delete', () => {
  const { confirmed, kept } = asked()

  fireEvent.click(screen.getByRole('button', { name: 'Delete session' }))

  expect(confirmed).toHaveBeenCalled()
  expect(kept).not.toHaveBeenCalled()
})

test('keeping it deletes nothing', () => {
  const { confirmed, kept } = asked()

  fireEvent.click(screen.getByRole('button', { name: 'Keep it' }))

  expect(kept).toHaveBeenCalled()
  expect(confirmed).not.toHaveBeenCalled()
})

test('escape and the page behind the card are both ways out', () => {
  /* The two the cited-source modal already answers to: a question with only one answer
     is one a reader who changed their mind is stuck in. */
  const first = asked()
  fireEvent.keyDown(document, { key: 'Escape' })
  expect(first.confirmed).not.toHaveBeenCalled()
  expect(first.kept).toHaveBeenCalled()
  cleanup()

  const second = asked()
  fireEvent.click(screen.getByRole('dialog').parentElement!)
  expect(second.confirmed).not.toHaveBeenCalled()
  expect(second.kept).toHaveBeenCalled()
})
